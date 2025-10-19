import efinance as ef
res = ef.stock.get_all_company_performance('2020-03-31')
print(res)