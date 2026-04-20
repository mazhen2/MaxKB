# coding=utf-8

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from application.api.application_api import SpeechToTextAPI
from common.auth import TokenAuth
from common.auth.authentication import has_permissions, get_is_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants, ViewPermission, CompareConstants
from common.log.log import log
from common.result import result, DefaultResultSerializer
from knowledge.api.knowledge_workflow import KnowledgeWorkflowApi, KnowledgeWorkflowActionApi, \
    KnowledgeWorkflowActionPageApi, KnowledgeWorkflowExportApi, KnowledgeWorkflowImportApi
from knowledge.serializers.common import get_knowledge_operation_object
from knowledge.serializers.knowledge_workflow import KnowledgeWorkflowSerializer, KnowledgeWorkflowActionSerializer, \
    KnowledgeWorkflowMcpSerializer


class KnowledgeDatasourceFormListView(APIView):
    authentication_classes = [TokenAuth]

    @has_permissions(
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND
        ),
    )
    def post(self, request: Request, workspace_id: str, knowledge_id: str, type: str, id: str):
        r = KnowledgeWorkflowSerializer.Datasource(
            data={'type': type, 'id': id, 'params': request.data, 'function_name': 'get_form_list'}
        ).action()

        return result.success(r)


class KnowledgeDatasourceView(APIView):
    authentication_classes = [TokenAuth]

    @has_permissions(
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND
        ),
    )
    def post(self, request: Request, workspace_id: str, knowledge_id: str, type: str, id: str, function_name: str):
        return result.success(KnowledgeWorkflowSerializer.Datasource(
            data={'type': type, 'id': id, 'params': request.data, 'function_name': function_name}).action())


# ... existing code ...
class KnowledgeWorkflowUploadDocumentView(APIView):
    # 设置认证方式为Token认证
    authentication_classes = [TokenAuth]

    # 使用drf-spectacular装饰器，用于生成OpenAPI文档
    @extend_schema(
        methods=['POST'],  # 注意：这里标记为GET但实际方法是POST，可能存在不一致
        description=_('Knowledge workflow upload document'),  # 接口描述
        summary=_('Knowledge workflow upload document'),  # 接口摘要
        operation_id=_('Knowledge workflow upload document'),  # 操作ID，用于API文档
        parameters=KnowledgeWorkflowActionApi.get_parameters(),  # 获取接口参数定义
        request=KnowledgeWorkflowActionApi.get_request(),  # 获取请求体定义
        responses=KnowledgeWorkflowActionApi.get_response(),  # 获取响应定义
        tags=[_('Knowledge Base')]  # API标签，用于文档分类
    )
    # 权限装饰器：配置多重权限校验规则
    @has_permissions(
        # 知识库文档创建的工作空间知识库权限
        PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_knowledge_permission(),
        # 知识库文档创建的工作空间管理角色权限
        PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_permission_workspace_manage_role(),
        # 工作空间管理员角色
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        # 自定义视图权限：用户角色 AND 知识库权限的组合校验
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],  # 用户角色列表
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],  # 知识库权限列表
            CompareConstants.AND  # 使用AND逻辑，需同时满足
        ),
    )
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        """
        处理文档上传的POST请求

        Args:
            request: HTTP请求对象，包含上传的文件数据
            workspace_id: 工作空间ID
            knowledge_id: 知识库ID

        Returns:
            返回统一的成功响应结果
        """
        # 实例化序列化器，传入工作空间和知识库ID
        # 调用upload_document方法处理文档上传逻辑
        # request.data包含上传的文件数据
        # request.user为当前登录用户
        # True参数可能表示是工作流模式上传
        return result.success(KnowledgeWorkflowActionSerializer(
            data={'workspace_id': workspace_id, 'knowledge_id': knowledge_id}).upload_document(request.data,
                                                                                               request.user, True))
# ... existing code ...



class KnowledgeWorkflowActionView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=['POST'],
        description=_('Knowledge workflow debug'),
        summary=_('Knowledge workflow debug'),
        operation_id=_('Knowledge workflow debug'),  # type: ignore
        parameters=KnowledgeWorkflowActionApi.get_parameters(),
        request=KnowledgeWorkflowActionApi.get_request(),
        responses=KnowledgeWorkflowActionApi.get_response(),
        tags=[_('Knowledge Base')]  # type: ignore
    )
    @has_permissions(
        PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND
        ),
    )
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(KnowledgeWorkflowActionSerializer(
            data={'workspace_id': workspace_id, 'knowledge_id': knowledge_id}).action(request.data, request.user, True))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            description=_('Page Knowledge workflow action'),
            summary=_('Page Knowledge workflow action'),
            operation_id=_('Page Knowledge workflow action'),  # type: ignore
            parameters=KnowledgeWorkflowActionApi.get_parameters(),
            request=KnowledgeWorkflowActionPageApi.get_request(),
            responses=KnowledgeWorkflowActionApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            ),
        )
        def get(self, request: Request, workspace_id: str, knowledge_id: str, current_page: int, page_size: int):
            return result.success(
                KnowledgeWorkflowActionSerializer(data={'workspace_id': workspace_id, 'knowledge_id': knowledge_id})
                .page(current_page, page_size, request.query_params))

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            description=_('Get knowledge workflow action'),
            summary=_('Get knowledge workflow action'),
            operation_id=_('Get knowledge workflow action'),  # type: ignore
            parameters=KnowledgeWorkflowActionApi.get_parameters(),
            responses=KnowledgeWorkflowActionApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            ),
        )
        def get(self, request, workspace_id: str, knowledge_id: str, knowledge_action_id: str):
            return result.success(KnowledgeWorkflowActionSerializer.Operate(
                data={'workspace_id': workspace_id, 'knowledge_id': knowledge_id, 'id': knowledge_action_id})
                                  .one())

    class Cancel(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['POST'],
            description=_('Cancel knowledge workflow action'),
            summary=_('Cancel knowledge workflow action'),
            operation_id=_('Cancel knowledge workflow action'),  # type: ignore
            parameters=KnowledgeWorkflowActionApi.get_parameters(),
            responses=DefaultResultSerializer(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_DOCUMENT_CREATE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            ),
        )
        def post(self, request, workspace_id: str, knowledge_id: str, knowledge_action_id: str):
            return result.success(KnowledgeWorkflowActionSerializer.Operate(
                data={'workspace_id': workspace_id, 'knowledge_id': knowledge_id, 'id': knowledge_action_id})
                                  .cancel())


class KnowledgeWorkflowView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=['POST'],
        description=_('Create knowledge workflow'),
        summary=_('Create knowledge workflow'),
        operation_id=_('Create knowledge workflow'),  # type: ignore
        parameters=KnowledgeWorkflowApi.get_parameters(),
        responses=KnowledgeWorkflowApi.get_response(),
        tags=[_('Knowledge Base')]  # type: ignore
    )
    @has_permissions(
        PermissionConstants.KNOWLEDGE_CREATE.get_workspace_permission(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(), RoleConstants.USER.get_workspace_role()
    )
    def post(self, request: Request, workspace_id: str):
        return result.success(KnowledgeWorkflowSerializer.Create(
            data={'user_id': request.user.id, 'workspace_id': workspace_id}
        ).save_workflow(request.data))

    class Publish(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['PUT'],
            description=_("Publishing an knowledge"),
            summary=_("Publishing an knowledge"),
            operation_id=_("Publishing an knowledge"),  # type: ignore
            parameters=KnowledgeWorkflowApi.get_parameters(),
            request=None,
            responses=DefaultResultSerializer,
            tags=[_('Knowledge')]  # type: ignore
        )
        @has_permissions(PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_knowledge_permission(),
                         PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_permission_workspace_manage_role(),
                         ViewPermission([RoleConstants.USER.get_workspace_role()],
                                        [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                                        CompareConstants.AND),
                         RoleConstants.WORKSPACE_MANAGE.get_workspace_role())
        @log(menu='Knowledge', operate='Publishing an knowledge',
             get_operation_object=lambda r, k: get_knowledge_operation_object(k.get('knowledge_id')))
        def put(self, request: Request, workspace_id: str, knowledge_id: str):
            return result.success(
                KnowledgeWorkflowSerializer.Operate(
                    data={'knowledge_id': knowledge_id, 'user_id': request.user.id,
                          'workspace_id': workspace_id, }).publish())

    class Export(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['GET'],
            description=_('Export knowledge workflow'),
            summary=_('Export knowledge workflow'),
            operation_id=_('Export knowledge workflow'),  # type: ignore
            parameters=KnowledgeWorkflowExportApi.get_parameters(),
            request=None,
            responses=KnowledgeWorkflowExportApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_WORKFLOW_EXPORT.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_WORKFLOW_EXPORT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            )
        )
        @log(menu='Knowledge', operate="Export knowledge workflow",
             get_operation_object=lambda r, k: get_knowledge_operation_object(k.get('knowledge_id')),
             )
        def get(self, request: Request, workspace_id: str, knowledge_id: str):
            return KnowledgeWorkflowSerializer.Export(
                data={'knowledge_id': knowledge_id, 'user_id': request.user.id, 'workspace_id': workspace_id}
            ).export()

    class Import(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['POST'],
            description=_('Import knowledge workflow'),
            summary=_('Import knowledge workflow'),
            operation_id=_('Import knowledge workflow'),  # type: ignore
            parameters=KnowledgeWorkflowImportApi.get_parameters(),
            request=KnowledgeWorkflowImportApi.get_request(),
            responses=KnowledgeWorkflowImportApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            )
        )
        @log(menu='Knowledge', operate="Import knowledge workflow",
             get_operation_object=lambda r, k: get_knowledge_operation_object(k.get('knowledge_id')),
             )
        def post(self, request: Request, workspace_id: str, knowledge_id: str):
            is_import_tool = get_is_permissions(request, workspace_id=workspace_id)(
                PermissionConstants.TOOL_IMPORT.get_workspace_permission(),
                PermissionConstants.TOOL_IMPORT.get_workspace_permission_workspace_manage_role(),
                RoleConstants.WORKSPACE_MANAGE.get_workspace_role(), RoleConstants.USER.get_workspace_role()
            )
            return result.success(KnowledgeWorkflowSerializer.Import(data={
                'knowledge_id': knowledge_id, 'user_id': request.user.id, 'workspace_id': workspace_id
            }).import_({'file': request.FILES.get('file')}, is_import_tool))

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        @extend_schema(
            methods=['PUT'],
            description=_('Edit knowledge workflow'),
            summary=_('Edit knowledge workflow'),
            operation_id=_('Edit knowledge workflow'),  # type: ignore
            parameters=KnowledgeWorkflowApi.get_parameters(),
            request=KnowledgeWorkflowApi.get_request(),
            responses=KnowledgeWorkflowApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_WORKFLOW_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            )
        )
        @log(
            menu='Knowledge Base', operate="Modify knowledge workflow",
            get_operation_object=lambda r, keywords: get_knowledge_operation_object(keywords.get('knowledge_id')),
        )
        def put(self, request: Request, workspace_id: str, knowledge_id: str):
            return result.success(KnowledgeWorkflowSerializer.Operate(
                data={'user_id': request.user.id, 'workspace_id': workspace_id, 'knowledge_id': knowledge_id}
            ).edit(request.data))

        @extend_schema(
            methods=['GET'],
            description=_('Get knowledge workflow'),
            summary=_('Get knowledge workflow'),
            operation_id=_('Get knowledge workflow'),  # type: ignore
            parameters=KnowledgeWorkflowApi.get_parameters(),
            responses=KnowledgeWorkflowApi.get_response(),
            tags=[_('Knowledge Base')]  # type: ignore
        )
        @has_permissions(
            PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_knowledge_permission(),
            PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            ViewPermission(
                [RoleConstants.USER.get_workspace_role()],
                [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
                CompareConstants.AND
            ),
        )
        def get(self, request: Request, workspace_id: str, knowledge_id: str):
            return result.success(KnowledgeWorkflowSerializer.Operate(
                data={'user_id': request.user.id, 'workspace_id': workspace_id, 'knowledge_id': knowledge_id}
            ).one())


class KnowledgeWorkflowVersionView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=['GET'],
        description=_('Get knowledge workflow version list'),
        summary=_('Get knowledge workflow version list'),
        operation_id=_('Get knowledge workflow version list'),  # type: ignore
        parameters=KnowledgeWorkflowApi.get_parameters(),
        responses=KnowledgeWorkflowApi.get_response(),
        tags=[_('Knowledge Base')]  # type: ignore
    )
    @has_permissions(
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND
        ),
    )
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(KnowledgeWorkflowSerializer.Operate(
            data={'user_id': request.user.id, 'workspace_id': workspace_id, 'knowledge_id': knowledge_id}
        ).one())


class McpServers(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(
        methods=['GET'],
        description=_("speech to text"),
        summary=_("speech to text"),
        operation_id=_("speech to text"),  # type: ignore
        parameters=SpeechToTextAPI.get_parameters(),
        request=SpeechToTextAPI.get_request(),
        responses=SpeechToTextAPI.get_response(),
        tags=[_('Knowledge Base')]  # type: ignore
    )
    @has_permissions(PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_application_permission(),
                     PermissionConstants.KNOWLEDGE_WORKFLOW_READ.get_workspace_permission_workspace_manage_role(),
                     ViewPermission([RoleConstants.USER.get_workspace_role()],
                                    [PermissionConstants.KNOWLEDGE.get_workspace_application_permission()],
                                    CompareConstants.AND),
                     RoleConstants.WORKSPACE_MANAGE.get_workspace_role())
    def post(self, request: Request, workspace_id, knowledge_id: str):
        return result.success(KnowledgeWorkflowMcpSerializer(
            data={'mcp_servers': request.query_params.get('mcp_servers'), 'workspace_id': workspace_id,
                  'user_id': request.user.id,
                  'knowledge_id': knowledge_id}).get_mcp_servers(request.data))
