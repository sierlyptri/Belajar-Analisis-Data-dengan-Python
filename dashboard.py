import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import urllib
import matplotlib.image as mpimg
from babel.numbers import format_currency

# Menyiapkan DataFrame
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)        
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english")["product_id"].count().reset_index()
    sum_order_items_df.rename(columns={
        "product_id": "product_count"
    }, inplace=True)
    sum_order_items_df = sum_order_items_df.sort_values(by='product_count', ascending=False)
    return sum_order_items_df

def review_score_df(df):
    review_scores = df['review_score'].value_counts().sort_values(ascending=False)
    return review_scores

# Plot map
def plot_map(data):
    brazil = mpimg.imread(urllib.request.urlopen('https://assets.puzzlefactory.pl/puzzle/340/961/original.jpg'),'jpg')
    ax = data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", figsize=(10,10), alpha=0.3,s=0.3,c='red')
    plt.axis('off')
    plt.imshow(brazil, extent=[-74.08283055, -33.8,-34.25116944,6.2])
    st.pyplot(fig=ax.figure)

# all_data dataset
all_data_df = pd.read_csv("./submission/dashboard/all_data.csv")

# geolocation dataset
geolocation_df = pd.read_csv('./submission/dashboard/customer_plotmap.csv')

datetime_columns = ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date", "order_purchase_timestamp", "shipping_limit_date"]
all_data_df.sort_values(by="order_approved_at", inplace=True)
all_data_df.reset_index(inplace=True)

for col in datetime_columns:
    all_data_df[col] = pd.to_datetime(all_data_df[col])

min_date = all_data_df["order_approved_at"].min()
max_date = all_data_df["order_approved_at"].max()

# Biar Gambar PP Bulet
st.markdown("""
  <style>
    div.st-emotion-cache-1xzhpx6:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > img:nth-child(1){
        border-radius: 50%;
    }
  </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Nama Pembuat
    st.title("Satria Harya Sulistyo")

    # PP Pembuat
    st.image("./submission/dashboard/doom.png")

    # Tanggal
    start_date, end_date = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Main
main_df = all_data_df[(all_data_df["order_approved_at"] >= str(start_date)) & 
                 (all_data_df["order_approved_at"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
review_scores = review_score_df(main_df)

# --Judul
st.header("Dashboard E-Commerce Brazil :convenience_store:")

# --Demografi Pelanggan
st.subheader("Persebaran Pelanggan")
tab1, tab2 = st.tabs(["Wilayah", "Peta Persebaran"])

with tab1:
    bystate_df = all_data_df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    bycity_df = all_data_df['customer_city'].value_counts().head(10)

    fig, ax = plt.subplots(1, 2, figsize=(28, 10))

    # Plot untuk customer_count berdasarkan negara bagian
    most_common_state = bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']
    bystate_df = bystate_df.sort_values(by='customer_count', ascending=False).head(10)
    sns.barplot(
        y='customer_state',
        x='customer_count',
        data=bystate_df,
        palette=["#b98d42" if state == most_common_state else "#D3D3D3" for state in bystate_df['customer_state']],
        ax=ax[0]
    )
    ax[0].set_title("Jumlah Pelanggan dari Tiap Negara Bagian", fontsize=15)
    ax[0].set_xlabel(None)
    ax[0].set_ylabel(None)

    # Plot untuk customer_count berdasarkan kota
    most_common_city = bycity_df.idxmax()
    bycity_df = bycity_df.sort_values(ascending=False).head(10)
    sns.barplot(
        y=bycity_df.index,
        x=bycity_df.values,
        palette=["#b98d42" if city == most_common_city else "#D3D3D3" for city in bycity_df.index],
        ax=ax[1]
    )
    ax[1].set_title("Jumlah Pelanggan dari Tiap Kota", fontsize=15)
    ax[1].set_xlabel(None)
    ax[1].set_ylabel(None)
    st.pyplot(fig)

with tab2:
    # Plotmap
    st.subheader("Peta Persebaran Pelanggan")
    plot_map(geolocation_df.drop_duplicates(subset='customer_unique_id'))

    with st.expander("Penjelasan"):
        st.write('Terlihat bahwa sebagian besar pelanggan tinggal di bagian Tenggara dan Selatan dari Brazil.')

# --Produk Paling Laku dan Paling Sepi Peminat
st.subheader("Popularitas Produk")

col1, col2 = st.columns(2)

with col1:
    total_items = sum_order_items_df["product_count"].sum()
    st.metric("Total Items:", total_items)

# Menghitung jumlah produk dan urutkan
sum_order_items_df = (
    all_data_df.groupby("product_category_name_english")["product_id"]
    .count()
    .reset_index()
    .rename(columns={"product_id": "products"})
    .sort_values(by="products", ascending=False)
)

# Membuat subplot dan menentukan warna
fig, axs = plt.subplots(1, 2, figsize=(12, 6))
colors = ["#b98d42", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

# Plot bar charts dengan formatting
top_5 = sum_order_items_df.head(5)
bottom_5 = sum_order_items_df.tail(5).sort_values(by="products", ascending=True)

sns.barplot(x="products", y="product_category_name_english", data=top_5, palette=colors, ax=axs[0])
axs[0].set_title("5 Produk Paling Laku", fontsize=16)

sns.barplot(x="products", y="product_category_name_english", data=bottom_5, palette=colors, ax=axs[1])
axs[1].set_title("5 Produk Paling Sepi Peminat", fontsize=16)

# Menghilangkan label yang tidak sesuai dan menyesuaikan layout
plt.suptitle("Ringkasan Popularitas Produk", fontsize=20, y=1.02)
for ax in axs.flat:
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.tick_params(bottom=False, left=False)
plt.tight_layout()

st.pyplot(fig)

# --Jumlah Pembelian
st.subheader("Pembelian")
tab1, tab2 = st.tabs(["Pesanan Harian", "Trend Bulanan"])
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        total_order = daily_orders_df["order_count"].sum()
        st.metric("Total Order:", value=total_order)

    with col2:
        total_revenue = format_currency(daily_orders_df["revenue"].sum(), "BRL", locale="pt_BR")
        st.metric("Total Revenue:", value=total_revenue)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        daily_orders_df["order_approved_at"],
        daily_orders_df["order_count"],
        marker="o",
        linewidth=2,
        color="#b98d42"
    )
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", labelsize=15)
    st.pyplot(fig)

with tab2:
    # Menghitung jumlah order unik per bulan dan mengubah index menjadi nama bulan
    monthly_order = all_data_df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "nunique",
    })
    monthly_order.index = monthly_order.index.strftime('%B')

    # Mereset index DataFrame dan mengubah nama kolom 'order_id' menjadi 'order_count'
    monthly_order = monthly_order.reset_index()
    monthly_order.rename(columns={
        "order_id": "order_count",
    }, inplace=True)

    # Mengurutkan data berdasarkan 'order_count' dan menghapus duplikasi berdasarkan 'order_approved_at'
    monthly_order = monthly_order.sort_values('order_count').drop_duplicates('order_approved_at', keep='last')

    # Mengubah index menjadi angka bulan dan mengurutkan data berdasarkan bulan
    monthly_order['month_numeric'] = pd.to_datetime(monthly_order['order_approved_at'], format='%B').dt.month
    monthly_order = monthly_order.sort_values('month_numeric')

    # Membuat line chart
    fig, ax = plt.subplots(figsize=(10, 5))
    plt.plot(monthly_order['order_approved_at'], monthly_order['order_count'], marker='o', linewidth=2, color="#b98d42")
    plt.title("Jumlah Pembelian per Bulan", fontsize=20)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --Review
st.subheader("Skor Penilaian")

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(
    x=review_scores.index,
    y=review_scores.values,
    order=[5.0, 4.0, 3.0, 2.0, 1.0],
    palette=["#b98d42" if score == 5.0 or score == 4.0 else "#D3D3D3" for score in review_scores.index]
)

plt.title("Jumlah Penilaian Pelanggan Terhadap Barang", fontsize=15)
plt.xlabel(None)
plt.ylabel(None)
plt.xticks(fontsize=12)
st.pyplot(fig)
