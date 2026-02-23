from app import create_app

# Lokaler Startpunkt, reicht so.
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
