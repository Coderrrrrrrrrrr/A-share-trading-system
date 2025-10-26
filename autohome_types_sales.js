/**
 * 使用 Puppeteer 抓取汽车之家品牌销量数据
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const xlsx = require('xlsx');

async function autoScroll(page){
  await page.evaluate(async () => {
    await new Promise((resolve, reject) => {
      let totalHeight = 0;
      const distance = 100;
      const timer = setInterval(() => {
        const scrollHeight = document.body.scrollHeight;
        window.scrollBy(0, distance);
        totalHeight += distance;

        if(totalHeight >= scrollHeight){
          clearInterval(timer);
          resolve();
        }
      }, 100);
    });
  });
}

async function fetchAutohomeSalesData(url) {
    /**
     * 获取汽车之家品牌销量数据
     * 
     * @param {string} url - 汽车之家销量榜页面URL
     * @returns {Array} 包含品牌排名、品牌名称和销量的数组
     */
    
    let browser;
    try {
        // 启动浏览器
        browser = await puppeteer.launch({ 
            headless: false, // 为了调试，先不使用headless模式
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
        
        // 打开新页面
        const page = await browser.newPage();
        
        // 设置用户代理，模拟真实浏览器
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        // 访问目标网页
        console.log('正在访问页面...');
        await page.goto(url, { 
            waitUntil: 'networkidle0', // 等待网络空闲
            timeout: 30000 
        });
        
        // 等待页面加载完成
        await page.waitForSelector('body', { timeout: 10000 });
        
        // 滚动页面以触发懒加载，确保所有数据都加载完成
        console.log('开始滚动页面以加载所有数据...');
        await autoScroll(page);
        
        // 等待一段时间确保动态内容加载完成
        await page.waitForTimeout(5000);
        
        // 提取销量数据
        const salesData = await page.evaluate(() => {
            const items = document.querySelectorAll('.tw-relative.tw-grid.tw-items-center.tw-grid-cols-\\[65px_168px_200px_auto_92px\\]');
            const data = [];
            
            items.forEach((item, index) => {
                try {
                    // 获取排名
                    const rankElement = item.querySelector('.tw-absolute .tw-min-w-\\[50px\\].tw-bg-\\[length\\:100\\%\\]');
                    const rank = rankElement ? rankElement.textContent.trim() : index + 1;
                    
                    // 获取车型名称
                    const brandElement = item.querySelector('.tw-flex.tw-flex-col .tw-text-nowrap.tw-text-lg');
                    const brand = brandElement ? brandElement.textContent.trim() : '未知车型';
                    
                    // 获取销量
                    const salesElement = item.querySelector('.tw-mx-4 .tw-pt-\\[5px\\] .tw-text-\\[18px\\].tw-font-bold');
                    const sales = salesElement ? salesElement.textContent.trim() : '0';
                    
                    data.push({
                        rank: parseInt(rank, 10),
                        brand: brand,
                        sales: parseInt(sales.replace(/\D/g, ''), 10) || 0
                    });
                } catch (err) {
                    console.error('解析单项数据出错:', err);
                }
            });
            
            return data;
        });
        
        return salesData;
        
    } catch (error) {
        console.error('抓取数据时出错:', error);
        return [];
    } finally {
        // 关闭浏览器
        if (browser) {
            await browser.close();
        }
    }
}

function saveToExcel(data, filename) {
    /**
     * 将数据保存到Excel文件
     * 
     * @param {Array} data - 销量数据数组
     * @param {string} filename - 保存的文件名
     */
    
    if (!data || data.length === 0) {
        console.log('没有数据可保存');
        return;
    }
    
    // 创建工作簿
    const wb = xlsx.utils.book_new();
    
    // 转换数据格式，添加日期列
    const wsData = [['日期', '排名', '车型', '销量'], ...data.map(item => [item.date, item.rank, item.brand, item.sales])];
    
    // 创建工作表
    const ws = xlsx.utils.aoa_to_sheet(wsData);
    
    // 将工作表添加到工作簿
    xlsx.utils.book_append_sheet(wb, ws, '汽车车型销量');
    
    // 写入文件
    xlsx.writeFile(wb, filename);
    console.log(`数据已保存到 ${filename}`);
}

async function main() {
    /**
     * 主函数
     */
    
    // 目标URL列表
    const urls = [
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-04.html",
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-05.html",
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-06.html",
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-07.html",
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-08.html",
        "https://www.autohome.com.cn/rank/1-1-0-0_9000-x-x-x/2025-09.html"
    ];
    
    console.log('正在获取汽车之家截至2025年9月车型销量数据...');
    
    // 存储所有数据
    const allSalesData = [];
    
    // 遍历所有URL并获取数据
    for (let i = 0; i < urls.length; i++) {
        const url = urls[i];
        const dateMatch = url.match(/(\d{4}-\d{2})\.html/);
        const date = dateMatch ? dateMatch[1] : `未知日期${i + 1}`;
        
        console.log(`正在处理 ${date} 的数据...`);
        
        try {
            // 获取销量数据
            const salesData = await fetchAutohomeSalesData(url);
            
            if (salesData && salesData.length > 0) {
                // 为每条数据添加日期信息
                salesData.forEach(item => {
                    item.date = date;
                });
                
                // 将数据添加到总数组中
                allSalesData.push(...salesData);
                console.log(`成功获取到 ${date} 的 ${salesData.length} 条销量数据`);
            } else {
                console.log(`${date} 未能获取到销量数据`);
            }
        } catch (error) {
            console.error(`处理 ${date} 数据时出错:`, error);
        }
        
        // 在请求之间添加延迟，避免过于频繁的请求
        if (i < urls.length - 1) {
            console.log('等待2秒后继续处理下一个链接...');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
    
    if (allSalesData.length > 0) {
        console.log(`总共成功获取到 ${allSalesData.length} 条销量数据`);
        
        // 按日期和排名排序
        allSalesData.sort((a, b) => {
            // 首先按日期排序
            if (a.date !== b.date) {
                return a.date.localeCompare(b.date);
            }
            // 然后按排名排序
            return a.rank - b.rank;
        });
        
        // 为每个月的数据重新分配排名
        let currentDate = '';
        let rankCounter = 1;
        
        allSalesData.forEach(item => {
            if (item.date !== currentDate) {
                currentDate = item.date;
                rankCounter = 1;
            }
            item.rank = rankCounter++;
        });
        
        // 显示部分数据作为示例
        console.log('前10条数据预览:');
        allSalesData.slice(0, 10).forEach(item => {
            console.log(`日期: ${item.date}, 排名: ${item.rank}, 车型: ${item.brand}, 销量: ${item.sales}`);
        });
        
        // 保存到Excel文件
        const filename = "./下载数据/汽车车型截至2025年9月销量数据.xlsx";
        saveToExcel(allSalesData, filename);
    } else {
        console.log('未能获取到任何销量数据，请检查网络连接或目标网站结构是否发生变化');
    }
}

// 运行主函数
if (require.main === module) {
    main().catch(console.error);
}

module.exports = {
    fetchAutohomeSalesData,
    saveToExcel,
    main
};