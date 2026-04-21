# coding=utf-8
import base64
import io
import time
import requests
from PIL import Image
from functools import reduce
from imghdr import what
from typing import List, Dict

from django.db.models import QuerySet
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from django.utils.translation import gettext_lazy as _
from application.flow.i_step_node import NodeResult, INode
from application.flow.step_node.image_understand_step_node.i_image_understand_node import IImageUnderstandNode
from application.flow.tools import Reasoning
from knowledge.models import File
from models_provider.tools import get_model_instance_by_model_workspace_id


def _resize_image(image_bytes: bytes, max_size: int = 768) -> bytes:
    """
    将图片缩放到 max_size 以内，减少视觉模型推理压力。
    始终通过 PIL 重新编码，确保输出是合法的图片数据。
    如果无法解析则返回 None。
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception:
        return None

    try:
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception:
        return None


def _extract_gif_frames(image_bytes: bytes, max_frames: int = 4, max_size: int = 768):
    """
    从 GIF 动画中均匀采样关键帧，每帧转为 PNG bytes。
    返回 List[bytes]（多帧 PNG），或 None（非动画 GIF / 解析失败）。
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return None

    if not getattr(img, 'is_animated', False) or img.n_frames <= 1:
        return None

    total = img.n_frames
    count = min(total, max_frames)
    # 均匀采样帧索引，包含首尾帧
    if count == 1:
        indices = [0]
    else:
        indices = [round(i * (total - 1) / (count - 1)) for i in range(count)]

    frames = []
    for idx in indices:
        try:
            img.seek(idx)
            frame = img.copy()
            if frame.mode in ('RGBA', 'LA', 'P'):
                frame = frame.convert('RGB')
            elif frame.mode != 'RGB':
                frame = frame.convert('RGB')

            if frame.width > max_size or frame.height > max_size:
                frame.thumbnail((max_size, max_size), Image.LANCZOS)

            buf = io.BytesIO()
            frame.save(buf, format='PNG')
            frames.append(buf.getvalue())
        except Exception:
            continue

    return frames if frames else None


def _write_context(node_variable: Dict, workflow_variable: Dict, node: INode, workflow, answer: str,
                   reasoning_content: str):
    chat_model = node_variable.get('chat_model')
    message_tokens = node_variable['usage_metadata']['output_tokens'] if 'usage_metadata' in node_variable else 0
    answer_tokens = chat_model.get_num_tokens(answer)
    node.context['message_tokens'] = message_tokens
    node.context['answer_tokens'] = answer_tokens
    node.context['answer'] = answer
    node.context['history_message'] = node_variable['history_message']
    node.context['question'] = node_variable['question']
    node.context['run_time'] = time.time() - node.context['start_time']
    node.context['reasoning_content'] = reasoning_content
    if workflow.is_result(node, NodeResult(node_variable, workflow_variable)):
        node.answer_text = answer


def write_context_stream(node_variable: Dict, workflow_variable: Dict, node: INode, workflow):
    """
    写入上下文数据 (流式)
    @param node_variable:      节点数据
    @param workflow_variable:  全局数据
    @param node:               节点
    @param workflow:           工作流管理器
    """
    response = node_variable.get('result')
    answer = ''
    reasoning_content = ''
    model_setting = node.context.get('model_setting',
                                     {'reasoning_content_enable': False, 'reasoning_content_end': '</think>',
                                      'reasoning_content_start': '<think>'})
    reasoning = Reasoning(model_setting.get('reasoning_content_start', '<think>'),
                          model_setting.get('reasoning_content_end', '</think>'))
    response_reasoning_content = False

    for chunk in response:
        if workflow.is_the_task_interrupted():
            break

        # 处理 reasoning content
        reasoning_chunk = reasoning.get_reasoning_content(chunk)
        content_chunk = reasoning_chunk.get('content')
        if 'reasoning_content' in chunk.additional_kwargs:
            response_reasoning_content = True
            reasoning_content_chunk = chunk.additional_kwargs.get('reasoning_content', '')
        else:
            reasoning_content_chunk = reasoning_chunk.get('reasoning_content')

        answer += content_chunk
        if reasoning_content_chunk is None:
            reasoning_content_chunk = ''
        reasoning_content += reasoning_content_chunk

        # 处理 chunk.content 为 list 的情况
        if isinstance(chunk.content, list):
            for chunk_item in chunk.content:
                text = chunk_item.get("text", "")
                yield {'content': text,
                       'reasoning_content': reasoning_content_chunk if model_setting.get('reasoning_content_enable',
                                                                                         False) else ''}
        else:
            text = chunk.content or ""
            yield {'content': text,
                   'reasoning_content': reasoning_content_chunk if model_setting.get('reasoning_content_enable',
                                                                                     False) else ''}

    reasoning_chunk = reasoning.get_end_reasoning_content()
    answer += reasoning_chunk.get('content')
    reasoning_content_chunk = ""
    if not response_reasoning_content:
        reasoning_content_chunk = reasoning_chunk.get(
            'reasoning_content')
    yield {'content': reasoning_chunk.get('content'),
           'reasoning_content': reasoning_content_chunk if model_setting.get('reasoning_content_enable',
                                                                             False) else ''}
    _write_context(node_variable, workflow_variable, node, workflow, answer, reasoning_content)


def write_context(node_variable: Dict, workflow_variable: Dict, node: INode, workflow):
    """
    写入上下文数据
    @param node_variable:      节点数据
    @param workflow_variable:  全局数据
    @param node:               节点实例对象
    @param workflow:           工作流管理器
    """
    response = node_variable.get('result')
    model_setting = node.context.get('model_setting',
                                     {'reasoning_content_enable': False, 'reasoning_content_end': '</think>',
                                      'reasoning_content_start': '<think>'})
    reasoning = Reasoning(model_setting.get('reasoning_content_start'), model_setting.get('reasoning_content_end'))
    reasoning_result = reasoning.get_reasoning_content(response)
    reasoning_result_end = reasoning.get_end_reasoning_content()
    content = reasoning_result.get('content') + reasoning_result_end.get('content')
    meta = {**response.response_metadata, **response.additional_kwargs}
    if 'reasoning_content' in meta:
        reasoning_content = (meta.get('reasoning_content', '') or '')
    else:
        reasoning_content = (reasoning_result.get('reasoning_content') or '') + (
                reasoning_result_end.get('reasoning_content') or '')
    _write_context(node_variable, workflow_variable, node, workflow, content, reasoning_content)


def file_id_to_base64(file_id: str):
    """
    将文件转换为 Base64 编码和图片格式。
    GIF 动画返回: [[base64_frame1, ...], 'gif_frames']
    静态图片返回: [base64_string, 'png']
    失败返回: None
    """
    try:
        file = QuerySet(File).filter(id=file_id).first()
        if not file:
            return None
        file_bytes = file.get_bytes()
        if not file_bytes:
            return None

        # GIF 动画：提取多帧
        frames = _extract_gif_frames(file_bytes)
        if frames:
            return [[base64.b64encode(f).decode("utf-8") for f in frames], 'gif_frames']

        # 静态图片：通过 PIL 验证和重编码
        image_bytes = _resize_image(file_bytes)
        if image_bytes is None:
            return None
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return [base64_image, 'png']
    except Exception as e:
        import logging
        logging.error(f"Failed to convert file {file_id} to base64: {str(e)}")
        return None


class BaseImageUnderstandNode(IImageUnderstandNode):
    def save_context(self, details, workflow_manage):
        self.context['answer'] = details.get('answer')
        self.context['question'] = details.get('question')
        self.context['exception_message'] = details.get('err_message')
        if self.node_params.get('is_result', False):
            self.answer_text = details.get('answer')

    def execute(self, model_id, system, prompt, dialogue_number, dialogue_type, history_chat_record, stream,
                model_params_setting,
                chat_record_id,
                image,
                model_id_type=None, model_id_reference=None,
                model_setting=None,
                **kwargs) -> NodeResult:
        if model_setting is None:
            model_setting = {'reasoning_content_enable': False, 'reasoning_content_end': '</think>',
                             'reasoning_content_start': '<think>'}
        self.context['model_setting'] = model_setting
        # 处理引用类型
        if model_id_type == 'reference' and model_id_reference:
            reference_data = self.workflow_manage.get_reference_field(
                model_id_reference[0],
                model_id_reference[1:],
            )
            if reference_data and isinstance(reference_data, dict):
                model_id = reference_data.get('model_id', model_id)
                model_params_setting = reference_data.get('model_params_setting')

        if model_id is None or model_id == '':
            raise Exception(_('Model is not allowed to be empty'))
        # 处理不正确的参数
        workspace_id = self.workflow_manage.get_body().get('workspace_id')
        image_model = get_model_instance_by_model_workspace_id(model_id, workspace_id,
                                                               **(model_params_setting or {}))
        # 执行详情中的历史消息不需要图片内容
        history_message = self.get_history_message_for_details(history_chat_record, dialogue_number)
        self.context['history_message'] = history_message
        question = self.generate_prompt_question(prompt)
        self.context['question'] = question.content
        # 生成消息列表, 真实的history_message
        message_list = self.generate_message_list(image_model, system, prompt,
                                                  self.get_history_message(history_chat_record, dialogue_number), image)
        self.context['message_list'] = message_list
        self.generate_context_image(image)
        self.context['dialogue_type'] = dialogue_type
        if stream:
            r = image_model.stream(message_list)
            return NodeResult({'result': r, 'chat_model': image_model, 'message_list': message_list,
                               'history_message': history_message, 'question': question.content}, {},
                              _write_context=write_context_stream)
        else:
            r = image_model.invoke(message_list)
            return NodeResult({'result': r, 'chat_model': image_model, 'message_list': message_list,
                               'history_message': history_message, 'question': question.content}, {},
                              _write_context=write_context)

    def generate_context_image(self, image):
        if isinstance(image, str) and image.startswith('http'):
            self.context['image_list'] = [{'url': image}]
        elif image is not None and len(image) > 0:
            self.context['image_list'] = image

    def get_history_message_for_details(self, history_chat_record, dialogue_number):
        start_index = len(history_chat_record) - dialogue_number
        history_message = reduce(lambda x, y: [*x, *y], [
            [self.generate_history_human_message_for_details(history_chat_record[index]),
             self.generate_history_ai_message(history_chat_record[index])]
            for index in
            range(start_index if start_index > 0 else 0, len(history_chat_record))], [])
        return history_message

    def generate_history_ai_message(self, chat_record):
        for val in chat_record.details.values():
            if self.node.id == val['node_id'] and 'image_list' in val:
                if val['dialogue_type'] == 'WORKFLOW':
                    return chat_record.get_ai_message()
                return AIMessage(content=val['answer'])
        return chat_record.get_ai_message()

    def generate_history_human_message_for_details(self, chat_record):
        for data in chat_record.details.values():
            if self.node.id == data['node_id'] and 'image_list' in data:
                image_list = data['image_list'] or []
                if len(image_list) == 0 or data['dialogue_type'] == 'WORKFLOW':
                    return HumanMessage(content=chat_record.problem_text)

                file_id_list = []
                url_list = []
                for image in image_list:
                    if 'file_id' in image:
                        file_id_list.append(image.get('file_id'))
                    elif 'url' in image:
                        url_list.append(image.get('url'))
                return HumanMessage(content=[
                    {'type': 'text', 'text': data['question']},
                    *[{'type': 'image_url', 'image_url': {'url': f'./oss/file/{file_id}'}} for file_id in file_id_list],
                    *[{'type': 'image_url', 'image_url': {'url': url}} for url in url_list]
                ])
        return HumanMessage(content=chat_record.problem_text)

    def get_history_message(self, history_chat_record, dialogue_number):
        start_index = len(history_chat_record) - dialogue_number
        history_message = reduce(lambda x, y: [*x, *y], [
            [self.generate_history_human_message(history_chat_record[index]),
             self.generate_history_ai_message(history_chat_record[index])]
            for index in
            range(start_index if start_index > 0 else 0, len(history_chat_record))], [])
        return history_message

    def generate_history_human_message(self, chat_record):

        for data in chat_record.details.values():
            if self.node.id == data['node_id'] and 'image_list' in data:
                image_list = data['image_list'] or []
                if len(image_list) == 0 or data['dialogue_type'] == 'WORKFLOW':
                    return HumanMessage(content=chat_record.problem_text)
                file_id_list = []
                url_list = []
                for image in image_list:
                    if 'file_id' in image:
                        file_id_list.append(image.get('file_id'))
                    elif 'url' in image:
                        url_list.append(image.get('url'))

                # 转换文件 ID 为 Base64，过滤掉失败的项
                image_base64_list = [
                    file_id_to_base64(file_id) for file_id in file_id_list
                ]
                image_base64_list = [img for img in image_base64_list if img is not None]

                # 构建 image_url 列表，支持 GIF 多帧
                image_url_items = []
                for base64_image in image_base64_list:
                    if not base64_image or len(base64_image) < 2 or not base64_image[1]:
                        continue
                    if base64_image[1] == 'gif_frames' and isinstance(base64_image[0], list):
                        for frame_b64 in base64_image[0]:
                            image_url_items.append({'type': 'image_url',
                                                    'image_url': {'url': f'data:image/png;base64,{frame_b64}'}})
                    else:
                        image_url_items.append({'type': 'image_url',
                                                'image_url': {'url': f'data:image/{base64_image[1]};base64,{base64_image[0]}'}})

                return HumanMessage(
                    content=[
                        {'type': 'text', 'text': data['question']},
                        *image_url_items,
                        *[{'type': 'image_url', 'image_url': {'url': url}} for url in url_list]
                    ])
        return HumanMessage(content=chat_record.problem_text)

    def generate_prompt_question(self, prompt):
        return HumanMessage(self.workflow_manage.generate_prompt(prompt))

    # 视频/非图片扩展名，在下载前直接跳过
    _SKIP_EXTENSIONS = {
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v',  # 视频
        'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a',                 # 音频
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar',  # 文档
    }

    @staticmethod
    def _fetch_image_as_base64(url: str):
        """
        下载 URL 图片，返回 (base64字符串, 格式) 或 None（不支持的格式或下载失败则跳过）
        支持的格式: jpeg, jpg, png, gif, webp
        自动跳过视频、音频、文档等非图片 URL
        """
        import logging
        logger = logging.getLogger(__name__)

        # 支持的图片格式
        supported_formats = {'jpeg', 'jpg', 'png', 'gif', 'webp'}

        # 第一步：从 URL 扩展名判断，跳过视频/音频/文档
        url_path = url.split('?')[0].split('#')[0]  # 去掉查询参数
        ext = url_path.rsplit('.', 1)[-1].lower() if '.' in url_path else ''
        if ext in BaseImageUnderstandNode._SKIP_EXTENSIONS:
            logger.info(f"Skipping non-image URL (extension: .{ext}): {url}")
            return None

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to fetch image from {url}: {str(e)}")
            return None

        content_type = resp.headers.get('Content-Type', '').split(';')[0].strip().lower()
        image_bytes = resp.content

        # 第二步：根据 Content-Type 跳过非图片资源
        if content_type and not content_type.startswith('image/') and content_type != 'application/octet-stream':
            logger.info(f"Skipping non-image content (Content-Type: {content_type}): {url}")
            return None

        # SVG 格式跳过（视觉模型不支持）
        if 'svg' in content_type or image_bytes.lstrip()[:5] in (b'<svg ', b'<?xml'):
            logger.warning(f"SVG format not supported: {url}")
            return None

        # 优先用响应头格式，回退到 imghdr
        if content_type.startswith('image/'):
            image_format = content_type[len('image/'):]
        else:
            image_format = what(None, image_bytes)

        # 验证格式
        if not image_format:
            logger.warning(f"Unable to detect image format, fallback to png: {url}")
            image_format = 'png'

        # 过滤 svg
        if image_format in ('svg+xml', 'svg'):
            return None

        # 验证格式是否支持
        if image_format not in supported_formats:
            logger.warning(f"Unsupported image format '{image_format}' from {url}")
            return None

        try:
            # GIF 动画：提取多帧
            if image_format == 'gif':
                frames = _extract_gif_frames(image_bytes)
                if frames:
                    return [base64.b64encode(f).decode("utf-8") for f in frames], 'gif_frames'
                # 非动画 GIF，走静态处理

            image_bytes = _resize_image(image_bytes)
            if image_bytes is None:
                logger.warning(f"Image data invalid or corrupted: {url}")
                return None
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return base64_image, 'png'
        except Exception as e:
            logger.error(f"Error processing image from {url}: {str(e)}")
            return None

    def _process_images(self, image):
        """
        处理图像数据，转换为模型可识别的格式
        支持的格式: jpeg, png, gif, webp
        自动跳过视频、音频等非图片资源
        """
        import logging
        logger = logging.getLogger(__name__)

        images = []
        # 支持的图片格式（OpenAI Vision API 支持）
        supported_formats = {'jpeg', 'jpg', 'png', 'gif', 'webp'}

        def _append_fetch_result(result):
            """将 _fetch_image_as_base64 的返回值追加到 images 列表"""
            if not result:
                return
            base64_data, fmt = result
            if fmt == 'gif_frames' and isinstance(base64_data, list):
                for frame_b64 in base64_data:
                    images.append({'type': 'image_url',
                                   'image_url': {'url': f'data:image/png;base64,{frame_b64}'}})
            else:
                images.append({'type': 'image_url',
                               'image_url': {'url': f'data:image/png;base64,{base64_data}'}})

        if isinstance(image, str) and image.startswith('http'):
            _append_fetch_result(self._fetch_image_as_base64(image))

        elif image is not None and len(image) > 0:
            for img in image:
                try:
                    if img.get('file_id'):
                        file_id = img['file_id']
                        file = QuerySet(File).filter(id=file_id).first()
                        if not file:
                            logger.warning(f"File not found: {file_id}")
                            continue

                        # 从文件名检查是否为非图片文件（视频/音频等），提前跳过
                        filename = getattr(file, 'file_name', '') or ''
                        if filename:
                            file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                            if file_ext in self._SKIP_EXTENSIONS:
                                logger.info(f"Skipping non-image file (extension: .{file_ext}): {filename}")
                                continue

                        raw_bytes = file.get_bytes()

                        # GIF 动画：提取多帧
                        if filename.lower().endswith('.gif'):
                            frames = _extract_gif_frames(raw_bytes)
                            if frames:
                                for f in frames:
                                    b64 = base64.b64encode(f).decode("utf-8")
                                    images.append({'type': 'image_url',
                                                   'image_url': {'url': f'data:image/png;base64,{b64}'}})
                                continue

                        # 静态图片
                        image_bytes = _resize_image(raw_bytes)
                        if image_bytes is None:
                            logger.warning(f"Image data invalid or corrupted for file: {file_id}")
                            continue

                        base64_image = base64.b64encode(image_bytes).decode("utf-8")
                        images.append(
                            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{base64_image}'}})

                    elif 'url' in img and img['url'].startswith('http'):
                        _append_fetch_result(self._fetch_image_as_base64(img['url']))

                except Exception as e:
                    logger.error(f"Error processing image {img}: {str(e)}")
                    continue

        return images

    def generate_message_list(self, image_model, system: str, prompt: str, history_message, image):
        prompt_text = self.workflow_manage.generate_prompt(prompt)
        images = self._process_images(image)

        if images:
            messages = [HumanMessage(content=[{'type': 'text', 'text': prompt_text}, *images])]
        else:
            messages = [HumanMessage(prompt_text)]

        if system is not None and len(system) > 0:
            return [
                SystemMessage(self.workflow_manage.generate_prompt(system)),
                *history_message,
                *messages
            ]
        else:
            return [
                *history_message,
                *messages
            ]

    @staticmethod
    def reset_message_list(message_list: List[BaseMessage], answer_text):
        result = [{'role': 'user' if isinstance(message, HumanMessage) else 'ai', 'content': message.content} for
                  message
                  in
                  message_list]
        result.append({'role': 'ai', 'content': answer_text})
        return result

    def get_details(self, index: int, **kwargs):
        return {
            'name': self.node.properties.get('stepName'),
            "index": index,
            'run_time': self.context.get('run_time'),
            'system': self.node_params.get('system'),
            'history_message': [{'content': message.content, 'role': message.type} for message in
                                (self.context.get('history_message') if self.context.get(
                                    'history_message') is not None else [])],
            'question': self.context.get('question'),
            'answer': self.context.get('answer'),
            'reasoning_content': self.context.get('reasoning_content'),
            'type': self.node.type,
            'message_tokens': self.context.get('message_tokens'),
            'answer_tokens': self.context.get('answer_tokens'),
            'status': self.status,
            'err_message': self.err_message,
            'image_list': self.context.get('image_list'),
            'dialogue_type': self.context.get('dialogue_type'),
            'enableException': self.node.properties.get('enableException'),
        }
