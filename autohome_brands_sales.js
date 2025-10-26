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
            headless: false, // 设置为false可以查看浏览器操作
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
        
        // 打开新页面
        const page = await browser.newPage();
        
        // 设置用户代理，模拟真实浏览器
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // 访问目标网页
        console.log('正在访问页面...');
        await page.goto(url, { 
            waitUntil: 'networkidle2',
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
            const data = [];
            
            // 查找包含销量数据的元素
            // 根据网页结构，查找包含销量数据的div元素
            const items = document.querySelectorAll('div.content');
            
            items.forEach((item) => {
                try {
                    // 查找品牌名称和销量
                    const brandElements = item.querySelectorAll('img');
                    const textElements = item.querySelectorAll('p, span, div');
                    
                    brandElements.forEach((img) => {
                        const brandName = img.alt;
                        if (brandName && !brandName.includes('logo') && !brandName.includes('icon')) {
                            // 在相邻文本中查找销量数字
                            const parentText = img.closest('div')?.textContent || '';
                            const salesMatch = parentText.match(/(\d+)/);
                            
                            if (salesMatch) {
                                const sales = parseInt(salesMatch[1], 10);
                                if (!isNaN(sales) && sales > 1000) { // 过滤掉太小的数字，可能是排名等
                                    // 避免重复添加
                                    if (!data.some(d => d.brand === brandName)) {
                                        data.push({
                                            rank: data.length + 1,
                                            brand: brandName,
                                            sales: sales
                                        });
                                    }
                                }
                            }
                        }
                    });
                } catch (e) {
                    // 忽略单个元素解析错误
                    console.warn('解析单项数据时出错:', e);
                }
            });
            
            // 如果没有通过上面方式获取到数据，尝试另一种方式
            if (data.length === 0) {
                // 查找所有可能包含品牌信息的元素
                const allItems = document.querySelectorAll('li, div.item, div.rank-list-item');
                
                allItems.forEach((item) => {
                    try {
                        // 查找品牌名称
                        const img = item.querySelector('img');
                        const brandName = img ? img.alt : null;
                        
                        if (brandName && brandName.length > 1 && brandName.length < 10) {
                            // 查找销量数字
                            const text = item.textContent || '';
                            const salesMatch = text.match(/(\d{4,})/); // 匹配4位以上的数字，通常是销量数据
                            
                            if (salesMatch) {
                                const sales = parseInt(salesMatch[1], 10);
                                if (!isNaN(sales) && sales > 1000) {
                                    // 避免重复添加
                                    if (!data.some(d => d.brand === brandName)) {
                                        data.push({
                                            rank: data.length + 1,
                                            brand: brandName,
                                            sales: sales
                                        });
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        // 忽略单个元素解析错误
                        console.warn('解析单项数据时出错:', e);
                    }
                });
            }
            
            // 如果仍然没有数据，使用更通用的方式
            if (data.length === 0) {
                // 直接获取页面所有文本内容，使用正则表达式匹配
                const pageText = document.body.innerText || document.body.textContent || '';
                const lines = pageText.split('\n');
                
                // 匹配模式：数字 + 品牌名称 + 销量数字
                const pattern = /(\d+)\s*([\u4e00-\u9fa5]{2,10})\s*(\d{4,})/g;
                let match;
                
                while ((match = pattern.exec(pageText)) !== null) {
                    const rank = parseInt(match[1], 10);
                    const brand = match[2];
                    const sales = parseInt(match[3], 10);
                    
                    if (!isNaN(rank) && !isNaN(sales) && sales > 1000) {
                        // 避免重复添加
                        if (!data.some(item => item.brand === brand)) {
                            data.push({
                                rank: data.length + 1,
                                brand: brand,
                                sales: sales
                            });
                        }
                    }
                }
            }
            
            // 按销量排序
            data.sort((a, b) => b.sales - a.sales);
            
            // 重新分配排名
            data.forEach((item, index) => {
                item.rank = index + 1;
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
    const wsData = [['日期', '排名', '品牌', '销量'], ...data.map(item => [item.date, item.rank, item.brand, item.sales])];
    
    // 创建工作表
    const ws = xlsx.utils.aoa_to_sheet(wsData);
    
    // 将工作表添加到工作簿
    xlsx.utils.book_append_sheet(wb, ws, '汽车品牌销量');
    
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
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-04.html",
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-05.html",
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-06.html",
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-07.html",
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-08.html",
        "https://www.autohome.com.cn/rank/1-3-1071-x/2025-09.html"
    ];
    
    console.log('正在获取汽车之家截至2025年9月品牌销量数据...');
    
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
        
        // 按日期和销量排序
        allSalesData.sort((a, b) => {
            // 首先按日期排序
            if (a.date !== b.date) {
                return a.date.localeCompare(b.date);
            }
            // 然后按销量排序
            return b.sales - a.sales;
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
            console.log(`日期: ${item.date}, 排名: ${item.rank}, 品牌: ${item.brand}, 销量: ${item.sales}`);
        });
        
        // 保存到Excel文件
        const filename = "./下载数据/汽车品牌截至2025年9月销量数据.xlsx";
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