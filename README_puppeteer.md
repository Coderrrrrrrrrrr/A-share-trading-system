# 使用 Puppeteer 抓取汽车之家销量数据

## 简介

本项目提供了一个使用 Puppeteer（Node.js）抓取汽车之家品牌销量数据的脚本。Puppeteer 是一个 Node.js 库，它提供了一个高级 API 来通过 DevTools 协议控制 Chrome 或 Chromium。

## 前置要求

在运行脚本之前，您需要安装以下软件：

1. **Node.js** (版本 14.0.0 或更高)
   - 访问 [Node.js 官网](https://nodejs.org/) 下载并安装
   
2. **npm** (通常随 Node.js 一起安装)

## 安装步骤

1. 打开命令行工具 (CMD, PowerShell, Terminal等)
2. 导航到项目目录：
   ```
   cd e:\PycharmProject\量化交易
   ```
3. 安装项目依赖：
   ```
   npm install
   ```

## 运行脚本

安装依赖后，可以通过以下命令运行脚本：
```
npm start
```

或者直接使用 Node.js 运行：
```
node autohome_brands_sales.js
```

## 脚本功能

该脚本会：
1. 使用 Puppeteer 启动无头浏览器
2. 访问汽车之家销量榜页面: https://www.autohome.com.cn/rank/1-3-1071-x/2025-04.html
3. 等待页面完全加载
4. 提取品牌销量数据
5. 按销量排序并重新分配排名
6. 将结果保存为 Excel 文件: `汽车品牌2025年4月销量数据_puppeteer.xlsx`

## 代码说明

### 主要函数

- `fetchAutohomeSalesData(url)`: 核心抓取函数，使用 Puppeteer 获取页面数据
- `saveToExcel(data, filename)`: 将数据保存为 Excel 文件
- `main()`: 主函数，协调整个抓取过程

### 技术特点

1. 使用无头浏览器，能够处理 JavaScript 动态渲染的内容
2. 设置了用户代理，模拟真实浏览器访问
3. 添加了适当的等待时间，确保页面加载完成
4. 包含错误处理机制，提高程序稳定性
5. 使用正则表达式和 DOM 查询相结合的方式提取数据
6. 自动排序并重新分配排名
7. 将结果保存为 Excel 格式，便于进一步分析

## 依赖包

- `puppeteer`: 控制无头浏览器的核心库
- `xlsx`: 用于生成 Excel 文件

## 注意事项

1. Puppeteer 在安装时会自动下载 Chromium，这可能需要一些时间
2. 首次运行时可能会比较慢，因为需要启动浏览器
3. 如果目标网站有反爬虫机制，可能需要调整等待时间和请求头
4. 确保网络连接稳定，以便成功加载页面