import os
from urllib.request import urlopen

url='localhost:8080/v'

resources = [
    '/wheelchair.html',
    '/actuator.html',
    '/index.html',
    '/IR_check_command.html',
    '/IR.html',
    '/light.html',
    '/timer.html',
    '/TV_A.html',
    '/TV.html',
]

path = os.path.dirname(os.path.abspath(__file__)) + '\\build'


def get_resource(resource):

    page = urlopen('http://%s%s' % (url, resource))

    # If the page is redirection, get the redirected page
    if page.geturl() != 'http://%s%s' % (url, resource):
        page = urlopen(page.geturl())

    return page.read().decode('utf-8')


def save_resource(resource, content):
    with open(resource, 'w') as f:
        f.write(content)

def main():
    for resource in resources:
        print('Exporting %s' % resource)
        print('Done ! Size: %d' % len(get_resource(resource)))
        save_resource(path + resource, get_resource(resource))
    
if __name__ == '__main__':
    main()