from appdir import app

# Start development web server
if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True)
