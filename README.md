## 介绍

本项目旨在抓取北京大学树洞中关于羽毛球场地的信息，并进行分析。

### 安装

1.  安装依赖：

    ```bash
    pip install -r requirements.txt
    ```

### 使用

3. 运行 `app.py` 启动整个应用：

    ```bash
    python app.py
    ```

    这个文件会同时运行 `fetcher.py` 和 `evaluator.py`，实现自动抓取、评估和筛选树洞帖子。

### 文件说明

*   `fetcher.py`: 负责从北京大学树洞抓取帖子，并将结果保存到 `treehole_posts.json` 文件中。
*   `evaluator.py`: 负责读取 `treehole_posts.json` 中的帖子，使用 OpenAI API 评估帖子内容是否与羽毛球场地相关，并将评估结果保存到 `evaluated_posts.json` 文件中。
*   `requirements.txt`: 包含了项目所需的 Python 依赖包。
*   `.gitignore`: 指定了 Git 仓库应该忽略的文件和目录。



