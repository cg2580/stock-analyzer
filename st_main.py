from time import sleep

import arrow
import streamlit as st
import tushare as ts

st.title('StocK Analyzer')

# hour_to_filter = st.slider('hour', 0, 23, 17)  # min: 0h, max: 23h, default: 17h

# st.title('请输入筛选条件 :blue[筛选条件] :sunglasses:')
st.header('请输入 :blue[筛选条件] :sunglasses:')

option_exchange = st.selectbox("exchange", ["SSE", "SZSE"])
option_market = st.selectbox("market", ["主板", "创业板"])

if st.button("Submit", type="primary"):
    start_date = arrow.now().shift(days=-30).format("YYYYMMDD")
    end_date = arrow.now().format("YYYYMMDD")
    exchange = option_exchange
    market = option_market
    print(f"数据取样区间：{start_date} - {end_date}, 交易所：{exchange}, 板块：{market}")
    result = []
    ts_codes_list = []
    if exchange == 'SZSE' and market == '创业板':
        with open('ts_codes/TS-CODES-SZSE-SECOND-BOARD', 'r') as file:
            ts_codes_list = [line.strip() for line in file]
    if exchange == 'SZSE' and market == '主板':
        with open('ts_codes/TS-CODES-SZSE-MAIN-BOARD', 'r') as file:
            ts_codes_list = [line.strip() for line in file]
    if exchange == 'SSE' and market == '主板':
        with open('ts_codes/TS-CODES-SSE-MAIN-BOARD', 'r') as file:
            ts_codes_list = [line.strip() for line in file]
    # 遍历股票代码，筛选符合条件的股票代码
    for ts_code in ts_codes_list:
        sleep(0.2)
        # 获取指定代码的股票日线行情信息，接口文档地址 https://tushare.pro/document/2?doc_id=27
        df = ts.pro_api().daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                fields='ts_code,trade_date,close,pre_close,vol')
        # 按交易日期对数据排序
        df = df.sort_values(by='trade_date', ascending=False).reset_index(drop=True)
        # print(df)
        # 排除交易数据不足5天的数据，排除收盘价大于50元的数据，排除收盘价低于昨收价的数据
        if len(df.index) < 5 or df.loc[0, 'close'] > 50 or df.loc[0, 'close'] < df.loc[0, 'pre_close']:
            continue
        # 判断(T)日5日线是否在10日线上方
        df_ma = ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date, ma=[5, 10, 20])
        is_t_minus_0_ma5_gt_ma10 = df_ma.loc[0, 'ma5'] > df_ma.loc[0, 'ma10']
        # 判断(T-1)日5日线是否在10日线上方
        is_t_minus_1_ma5_gte_ma10 = df_ma.loc[1, 'ma5'] >= df_ma.loc[1, 'ma10']
        # 判断(T-1)日5日线是否在10日线下方
        is_t_minus_1_ma5_lt_ma10 = df_ma.loc[1, 'ma5'] < df_ma.loc[1, 'ma10']
        # 判断当日成交量是否大于前4日每天的成交量
        is_vol_up_a = False
        is_vol_up_a_series = df.loc[0, "vol"] > df.loc[1:4, "vol"]
        if len(set(is_vol_up_a_series)) == 1:
            is_vol_up_a = set(is_vol_up_a_series).pop()
        # 判断(T-1)日成交量是否大于(T-2)~(T-5)日每天的成交量
        is_vol_up_b = False
        is_vol_up_b_series = df.loc[1, "vol"] > df.loc[2:5, "vol"]
        if len(set(is_vol_up_b_series)) == 1:
            is_vol_up_b = set(is_vol_up_b_series).pop()
        # 判断(T-2)日成交量是否大于(T-3)~(T-5)日每天的成交量（连续3天放量）
        is_vol_up_c = False
        is_vol_up_c_series = df.loc[2, "vol"] > df.loc[3:5, "vol"]
        if len(set(is_vol_up_c_series)) == 1:
            is_vol_up_c = set(is_vol_up_c_series).pop()
        # 输出符合条件的股票代码
        # if is_vol_up_a and is_vol_up_b and is_vol_up_c:  # 连续三天放量
        # 连续两天放量，T日5日线在10日线上方，T-1日5日线在10日线下方
        # if is_vol_up_a and is_vol_up_b and is_vol_up_c and is_t_minus_0_ma5_gt_ma10 and is_t_minus_1_ma5_lt_ma10:
        # 只看是否放量
        if is_vol_up_a and is_vol_up_b and is_vol_up_c:
            # print(df.loc[0, "ts_code"])
            st.write(df.loc[0, "ts_code"])
            result.append(df.loc[0, "ts_code"])
    st.write(result)
