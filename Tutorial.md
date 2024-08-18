
# Python 开发环境搭建教程

## 1. 安装 VSCode

VSCode 是一个常用的代码编辑工具，你可以通过以下链接下载并安装：[下载 VSCode](https://code.visualstudio.com)

## 2. 安装 Python

在网上找到相应的教程，按照步骤安装 Python。

## 3. 安装 Git

Git 是一个用于代码协作的工具，点击以下链接下载并安装：[下载 Git](https://git-scm.com)

安装完成后，在命令行中设置你的身份信息：
```sh
git config --global user.name '你的名字' 
git config --global user.email '你的邮箱'
```

## 4. 使用 VSCode 打开项目文件夹

用 VSCode 打开一个空文件夹，作为你的开发项目目录。

## 5. 新建 Python 文件

在项目目录中新建一个后缀为 `.py` 的空白 Python 文件。

## 6. 创建 Python 虚拟环境

点击 VSCode 右下角创建一个 Python 虚拟开发环境。不同的项目需要不同的工具，使用虚拟环境可以在开发多个应用时区分所需工具，避免安装无用工具占用空间。

## 7. 安装依赖及开发工具包

### 1.智谱AI开发工具包
按照智谱开发的说明书（接口文档）操作，打开命令行（`Ctrl+J`）并粘贴以下命令安装必要的工具：
```sh
pip install zhipuai
```
接口文档：[智谱 AI API 文档](https://bigmodel.cn/dev/api)

### 2.安装FLASK后端工具
本AI工具使用浏览器作为交互。为了在浏览器上方便调用AI API。我们选择了轻量级的后端框架（也就是让网站运行起来的工具）——`Flask`。此外，工具还使用浏览器的API来实现录音输入，简化了整个流程。同样跟刚才一样，运作以下命令：

```sh
pip install flask flask-cors
```

## 8. 测试代码

在新建的 Python 文件中粘贴以下代码，测试是否正常运行：
```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="") # 请填写您自己的APIKey

response = client.chat.completions.create(
    model="glm-4",  # 填写需要调用的模型名称
    messages=[
        {"role": "user", "content": "你好！你叫什么名字"},
    ],
    stream=False,
    )
print(response.choices[0].message.content.strip())
```
如果有正确的结果，恭喜你成功调用了 AI！接下来可以完成自定义工具。

接下来是

## 9.下载代码
粘贴下面代码到命令行运行
```sh
git clone https://gitee.com/cjwn/build_ai_tool_tutorial.git
```

## 10.环境变量设置
将ZHIPUAI APIKEY添加至系统环境变量（ZHIPU_APP_KEY）。
### Windows

1. 打开 `系统属性` 窗口，方法是按下 `Win + Pause/Break` 键或在控制面板中搜索 `系统`。
2. 点击左侧的 `高级系统设置`，然后点击 `环境变量`。
3. 在 `系统变量` 部分，点击 `新建`。
4. 在 `变量名` 中输入 `ZHIPU_APP_KEY`，在 `变量值` 中输入你的 APIKey。
5. 点击 `确定` 保存更改，然后关闭所有对话框。


### macOS

1. 打开 `Terminal`。
2. 使用以下命令打开 `.bash_profile` 或 `.zshrc` 文件（取决于你使用的是 Bash 还是 Zsh）：
   ```sh
   nano ~/.bash_profile  # 如果你使用的是 Bash。老版本macOS系统使用
   nano ~/.zshrc  # 如果你使用的是 Zsh
   ```
3. 在文件末尾添加以下内容：
   ```sh
   export ZHIPU_APP_KEY="你的APIKey"
   ```
4. 保存并退出编辑器，然后运行以下命令使更改生效：
   ```sh
   source ~/.bash_profile  # Bash 用户。老版本macOS系统使用
   source ~/.zshrc  # Zsh 用户
   ```

通过上述步骤，你已成功将 ZHIPUAI 的 APIKey 添加到系统的环境变量中。在项目中调用 API 时，环境变量会自动加载这个 APIKey。方便你提交代码时，不会将API KEY也一并提交上去。

## 11.运行.py文件

### 1.运行命令行
打开VS终端，输入python sample.py运行，查看返回结果

### 2.运行网页版
点击右上角播放按钮运行server.py 将启动flask的后端服务器。按ctrl（win）或command（Mac）打开输出的http://127.0.0.1:5000将启动网页，打开麦克风即可进行语音输入。

细心的你有没有发现，目前网页版返回的结果有点慢？而且是一次性输出的？ 跟目前用的AI工具返回的样子不太一样？而当刚才运行sample输出的时候却是一个字一个字地像是真·AI工具那样？

网页这样的情况不太令人满意，你不会停下来的，对吗？现在我们顺便学下如何切换到另外一个分支。

## 12.切换分支
终端运行git checkout -b sse origin/sse