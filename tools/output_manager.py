"""
输出管理工具 - 按日期和项目分类保存任务结果
"""
import os
from datetime import datetime
from pathlib import Path
from core import tool, BaseTool, ToolResult


@tool(tags=["output", "file", "management"], description="管理任务执行结果的保存位置和分类")
class OutputManagerTool(BaseTool):
    """输出管理工具 - 管理任务结果的保存位置和分类"""
    
    @property
    def name(self) -> str:
        return "OutputManagerTool"
    
    @property
    def description(self) -> str:
        return """管理任务执行结果的保存位置。
支持按日期和项目分类保存：
- 自动创建日期目录（YYYY-MM-DD 格式）
- 支持项目子目录
- 返回保存路径供后续使用"""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "项目名称，用于创建项目子目录（可选）"
                },
                "filename": {
                    "type": "string",
                    "description": "文件名（不含路径，可选）"
                },
                "content": {
                    "type": "string",
                    "description": "要保存的内容（可选，如果提供则自动保存）"
                },
                "file_type": {
                    "type": "string",
                    "enum": ["txt", "md", "json", "log"],
                    "description": "文件类型（默认：txt）"
                }
            },
            "required": []
        }
    
    def execute(
        self,
        project: str = None,
        filename: str = None,
        content: str = None,
        file_type: str = "txt",
        **kwargs
    ) -> ToolResult:
        """
        执行输出管理
        
        Args:
            project: 项目名称
            filename: 文件名
            content: 保存内容
            file_type: 文件类型
        """
        # 获取输出根目录
        from core.config_loader import get_config
        config = get_config()
        output_root = config.get('directories.output', './output')
        
        # 确保输出根目录存在
        os.makedirs(output_root, exist_ok=True)
        
        # 构建目录路径
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(output_root, today)
        
        # 如果有项目名，创建项目子目录
        if project:
            project_dir = os.path.join(date_dir, project)
            os.makedirs(project_dir, exist_ok=True)
            base_dir = project_dir
        else:
            base_dir = date_dir
        
        # 生成文件名
        if filename:
            # 使用提供的文件名
            if not filename.endswith(f'.{file_type}'):
                filename = f"{filename}.{file_type}"
        else:
            # 自动生成文件名
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"task_{timestamp}.{file_type}"
        
        # 完整文件路径
        file_path = os.path.join(base_dir, filename)
        
        # 如果提供了内容，保存文件
        if content:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                output=f"文件已保存至：{file_path}\n项目：{project or '未分类'}\n日期：{today}"
            )
        else:
            # 仅返回路径信息
            return ToolResult(
                success=True,
                output=f"输出目录准备就绪\n日期目录：{date_dir}\n项目目录：{base_dir}\n建议文件名：{filename}"
            )


# 注册工具
def register_output_manager():
    """注册输出管理工具"""
    from core.resource import repo
    repo.register_tool("OutputManagerTool", OutputManagerTool)
