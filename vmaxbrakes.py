import requests
from bs4 import BeautifulSoup
import csv
import json
import re

baseurl = 'https://www.vmaxbrakes.com.au/part-finder/'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43'
}
data = []
fields = ['Category (Parent)', 'Category URL (Parent)', 'Category - Leaf (Child 1)', 'Category URL - Leaf (Child 1)', 'Product URL', 'PartNumber', 'Product Title', 'Product Subtitle', 'Product Description', 'Image URLs', 'Price', 'List of Vehicle Compatibility', 'Brand','OE number / cross-reference' ]
filename = 'vmaxbrakes.csv'

r = requests.get(baseurl, headers=headers)
soup = BeautifulSoup(r.content, 'lxml')

processed_urls = set()


selectOption = soup.find('select', id='clist_11_1')

productList = []
for option in selectOption:
    make = option.text.lower().replace(' ', '-')
    url = baseurl + make

    if url not in processed_urls:
        productList.append(url)
        processed_urls.add(url)

urlList =  productList[2:]

for makeUrl in urlList:
    print(makeUrl)
    page_num_model = 1
    while True:
        page_url_model = makeUrl + f'/?pgnum={page_num_model}'
        r = requests.get(page_url_model, headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')
        print(page_url_model)

        urlModels = soup.find_all('div', {'class': 'panel panel-default'})

        if not urlModels:
            break  

        listProductURL = []

        if urlModels is not None:
            for urlModel in urlModels:
                linkProduct = urlModel.find('a', href=True)
                if linkProduct is not None:
                    productURLItem = linkProduct['href']
                    if productURLItem not in processed_urls:
                        listProductURL.append(productURLItem)
                        processed_urls.add(productURLItem)
        # print(listProductURL)

        for productURL in listProductURL:
            r  = requests.get(productURL, headers=headers)
            soup = BeautifulSoup(r.content, 'lxml')

            try:
                productTitle = soup.find('h1', {'itemprop':'name'}).text.strip()
            except:
                productTitle = ''

            try:
                productDescription_ = soup.find('div', class_='productdetails').text.strip().replace('Powered by eBay Turbo Lister','').replace('Copywrite notice; All information and pictures on this page are the property of Stefkovic Pty Ltd 2013 and may not be distributed or commercially exploited, copied, reproduced fully or partially in any way.','').replace('GST is include in the price, all goods sold are provided with a Tax invoice.','').replace('Click in the postage calculator tab under the picture to work out postage costs for delivery.','').replace('We supply all models, if you cannot find what you are looking for please contact us.','').replace('The picture is used for illustration purposes only.','').replace('Copyright notice; All information and pictures on this page are the property of Stefkovic Pty Ltd and VMAX™ 2018 and may not be distributed or commercially exploited, copied, reproduced fully or partially in any way.', '').replace('We carry many makes and models rotors and pads in stock, please do not hesitate to contact us if the part your after is not listed.','').replace('Copyright notice© ; All information and pictures on this page are the property of Stefkovic Pty Ltd 2014 and may not be distributed or commercially exploited, copied, reproduced fully or partially in any way.','').replace('Please also contact us if you require brake pads.','').replace('Please feel free to contact us if you cannot find any other pads your after.','')
                productDescription = re.sub(r'\s{2,}', '\n', productDescription_)
            except:
                productDescription = ''

            try:
                partNumber = soup.find('span', {'itemprop':'productID'}).text.strip().replace('SKU:','')
            except:
                partNumber = ''
            
            try:
                price = soup.find('div', {'itemprop':'price'} , class_='productprice productpricetext').text.strip().replace('$','')
            except:
                price = ''
            
            try:
                imgproductmedia = soup.find('div', {'class': 'main-image text-center'})
                a_Image = imgproductmedia.find('a', class_='fancybox')
                if a_Image:
                    image_Url = 'https://www.vmaxbrakes.com.au' + a_Image['href']                    
            except:
                imgproductmedia = ''
            
            try:
                table = soup.find_all('div', class_='productdetails')[1] 
                brand = table.find_all('tr')[1]
            except:
                table =  ''

            try:
                breadcrumb = soup.find('ul', class_='breadcrumb')
                txtbreadcrumb = breadcrumb.find_all('a')
                if len(txtbreadcrumb) >= 4:
                    make_ = txtbreadcrumb[1].text.strip()
                    model_ = txtbreadcrumb[2].text.strip()

                Vehicle_Compatibility = []
                Vehicle_Compatibility.append({
                    "make": make_,
                    "Model": model_,
                })

                list_of_Vehicle_Compatibility = json.dumps(Vehicle_Compatibility)
            except:
                breadcrumb =  ''
            
            vmaxbrakes = {
                'Category (Parent)': 'Home   ' + make_ ,
                'Category URL (Parent)': makeUrl,
                'Category - Leaf (Child 1)': 'Home   ' + make_ + '   '+ model_,
                'Category URL - Leaf (Child 1)': makeUrl+'/'+model_+'/',
                'Product URL': productURL,
                'PartNumber': partNumber,
                'Product Title': productTitle, 
                'Product Subtitle': '',
                'Product Description': productDescription,
                'Image URLs': image_Url,
                'Price': price,
                'Brand': brand.text.replace('Brand','').replace('\n',''),
                'List of Vehicle Compatibility': list_of_Vehicle_Compatibility.replace('[{', '{').replace('}]', '}'),                
            }
            data.append(vmaxbrakes)
            print('Saving',  vmaxbrakes['PartNumber'], vmaxbrakes['Price'], vmaxbrakes['Brand'], vmaxbrakes['Category URL - Leaf (Child 1)'] , vmaxbrakes['Category (Parent)'],  vmaxbrakes['Product URL'],vmaxbrakes['Product Title'])
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                for item in data:
                    writer.writerow(item)
        
        page_num_model += 1
