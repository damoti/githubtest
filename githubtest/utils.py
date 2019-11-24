import bs4
import requests


def get_form_data(html=None, form=None, **kwargs):
    if form is None:
        soup = bs4.BeautifulSoup(html, 'html5lib')
        form = soup.find('form', **kwargs)
    data = {}
    for input in form.find_all('input'):
        if 'name' in input.attrs and 'value' in input.attrs:
            data[input['name']] = input['value']
    return data


def get_external_ip():
    return requests.get('https://api.ipify.org').text
