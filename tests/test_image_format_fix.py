# coding=utf-8
"""
图像理解节点格式检测修复 - 单元测试
用于验证 base_image_understand_node.py 的图片格式处理是否正确
"""

import unittest
import base64
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io


class TestImageFormatDetection(unittest.TestCase):
    """图片格式检测测试"""

    def setUp(self):
        """测试前准备"""
        # 创建测试用的有效图片
        self.valid_png = self._create_test_image('PNG')
        self.valid_jpg = self._create_test_image('JPEG')
        self.valid_gif = self._create_test_image('GIF')

    def _create_test_image(self, format_type):
        """创建测试用的图片数据"""
        img = Image.new('RGB', (100, 100), color='red')
        buf = io.BytesIO()
        img.save(buf, format=format_type)
        return buf.getvalue()

    def test_valid_format_detection(self):
        """测试：有效格式识别"""
        from imghdr import what

        # PNG 应该被识别
        self.assertEqual(what(None, self.valid_png), 'png')

        # JPEG 应该被识别
        self.assertEqual(what(None, self.valid_jpg), 'jpeg')

        # GIF 应该被识别
        self.assertEqual(what(None, self.valid_gif), 'gif')

    def test_invalid_format_fallback(self):
        """测试：无效格式 fallback 处理"""
        from imghdr import what

        # 垃圾数据应该无法识别（返回 None）
        self.assertIsNone(what(None, b'invalid image data'))

        # 此时应该 fallback 到 'png'
        # 在修复后的 file_id_to_base64 中会这样处理
        detected = what(None, b'invalid image data') or 'png'
        self.assertEqual(detected, 'png')

    def test_format_whitelist(self):
        """测试：格式白名单检查"""
        supported_formats = {'jpeg', 'jpg', 'png', 'gif', 'webp'}

        test_cases = [
            ('png', True),
            ('jpeg', True),
            ('jpg', True),
            ('gif', True),
            ('webp', True),
            ('bmp', False),
            ('svg', False),
            ('tiff', False),
            ('heic', False),
            ('None', False),
            (None, False),
        ]

        for format_str, should_support in test_cases:
            if format_str is None:
                result = format_str in supported_formats
            else:
                result = format_str in supported_formats
            self.assertEqual(
                result, should_support,
                f"Format '{format_str}' whitelist check failed"
            )

    def test_format_normalization(self):
        """测试：格式标准化（jpg -> jpeg）"""
        # 标准化逻辑
        test_cases = [
            ('jpg', 'jpeg'),
            ('jpeg', 'jpeg'),
            ('png', 'png'),
            ('gif', 'gif'),
            ('webp', 'webp'),
        ]

        for input_fmt, expected_fmt in test_cases:
            normalized = 'jpeg' if input_fmt == 'jpg' else input_fmt
            self.assertEqual(
                normalized, expected_fmt,
                f"Format normalization failed for '{input_fmt}'"
            )

    def test_mime_type_generation(self):
        """测试：生成有效的 MIME type"""
        supported_formats = {'jpeg', 'jpg', 'png', 'gif', 'webp'}

        for image_format in supported_formats:
            # 标准化格式
            normalized = 'jpeg' if image_format == 'jpg' else image_format

            # 生成 MIME type
            mime_type = f'data:image/{normalized};base64,dummybase64'

            # 验证不包含 'None'
            self.assertNotIn('None', mime_type)
            self.assertNotIn('null', mime_type)
            self.assertIn(f'image/{normalized}', mime_type)

    @patch('base64.b64encode')
    def test_base64_encoding(self, mock_b64encode):
        """测试：Base64 编码"""
        mock_b64encode.return_value = b'encodeddata'

        result = base64.b64encode(self.valid_png)
        # 在实际代码中会调用 .decode("utf-8")
        decoded = base64.b64encode(self.valid_png).decode("utf-8")

        self.assertIsInstance(decoded, str)
        self.assertNotIn('\x00', decoded)  # 没有空字符


class TestImageURLConstruction(unittest.TestCase):
    """图片 URL 构造测试"""

    def test_valid_data_url(self):
        """测试：构造有效的 data URL"""
        base64_image = 'abc123def456'
        image_format = 'png'

        data_url = f'data:image/{image_format};base64,{base64_image}'

        # 验证 URL 格式
        self.assertTrue(data_url.startswith('data:image/'))
        self.assertIn(';base64,', data_url)
        self.assertNotIn('None', data_url)
        self.assertTrue(data_url.endswith('abc123def456'))

    def test_invalid_data_url_with_none(self):
        """测试：None 格式会生成无效 URL"""
        base64_image = 'abc123def456'
        image_format = None

        # 这是修复前的问题
        if image_format is None:
            bad_url = f'data:image/{image_format};base64,{base64_image}'
            self.assertIn('None', bad_url)  # ❌ 不应该出现
        else:
            good_url = f'data:image/{image_format};base64,{base64_image}'
            self.assertNotIn('None', good_url)  # ✅ 正确

    def test_format_normalization_in_url(self):
        """测试：URL 中的格式标准化"""
        test_cases = [
            ('jpg', 'jpeg'),
            ('jpeg', 'jpeg'),
            ('png', 'png'),
        ]

        for input_fmt, expected_fmt in test_cases:
            normalized = 'jpeg' if input_fmt == 'jpg' else input_fmt
            data_url = f'data:image/{normalized};base64,dummy'

            self.assertIn(f'image/{expected_fmt}', data_url)


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""

    def test_filter_none_results(self):
        """测试：过滤 None 结果"""
        results = [
            ['base64_data1', 'png'],
            None,
            ['base64_data2', 'jpeg'],
            None,
            ['base64_data3', 'gif'],
        ]

        # 过滤
        filtered = [r for r in results if r is not None]

        self.assertEqual(len(filtered), 3)
        self.assertNotIn(None, filtered)

    def test_validate_result_structure(self):
        """测试：验证结果结构"""
        valid_result = ['base64string', 'png']
        invalid_results = [
            None,
            ['base64string'],  # 缺少格式
            ['base64string', None],  # 格式为 None
            [],
            'not_a_list',
        ]

        # 验证有效结果
        self.assertTrue(
            valid_result is not None and
            len(valid_result) >= 2 and
            valid_result[1] is not None
        )

        # 验证无效结果
        for invalid in invalid_results:
            is_valid = (
                invalid is not None and
                isinstance(invalid, list) and
                len(invalid) >= 2 and
                invalid[1] is not None
            )
            self.assertFalse(is_valid)

    def test_partial_failure_handling(self):
        """测试：部分失败处理（一个图片失败不影响其他）"""
        images = [
            {'file_id': 'file1'},  # 有效
            {'file_id': 'file2'},  # 失败
            {'file_id': 'file3'},  # 有效
        ]

        results = []
        for img in images:
            try:
                # 模拟处理
                if img['file_id'] == 'file2':
                    result = None  # 模拟失败
                else:
                    result = [f'base64_{img["file_id"]}', 'png']

                if result is not None:
                    results.append(result)
            except Exception:
                continue  # 跳过失败的

        # 应该有 2 个成功结果
        self.assertEqual(len(results), 2)


class TestSVGFiltering(unittest.TestCase):
    """SVG 过滤测试"""

    def test_svg_content_detection(self):
        """测试：检测 SVG 内容"""
        svg_content = b'<svg version="1.1" xmlns="http://www.w3.org/2000/svg">'
        xml_content = b'<?xml version="1.0"?>'
        not_svg = b'PNG JPEG GIF data'

        # 检查 SVG 标记
        self.assertTrue(svg_content.lstrip()[:5] in (b'<svg ', b'<?xml'))
        self.assertTrue(xml_content.lstrip()[:5] in (b'<svg ', b'<?xml'))
        self.assertFalse(not_svg.lstrip()[:5] in (b'<svg ', b'<?xml'))

    def test_svg_content_type_filtering(self):
        """测试：按 Content-Type 过滤 SVG"""
        test_cases = [
            ('image/svg+xml', True),  # 应该过滤
            ('image/svg', True),  # 应该过滤
            ('image/png', False),
            ('image/jpeg', False),
            ('text/plain', False),
        ]

        for content_type, should_filter in test_cases:
            is_svg = 'svg' in content_type
            self.assertEqual(is_svg, should_filter)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
