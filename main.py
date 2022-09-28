'''

TODO:
    - add option to send request to make account admin/senior
    - implement language slection in scraper form
    - twitter for only some users
    - get the form to work

'''

from apps import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)