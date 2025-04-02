import os
from web import app, BASE_DIR

if __name__ == '__main__':
    # Configurar un PIN fijo para el debugger
    os.environ['WERKZEUG_DEBUG_PIN'] = '123-456-789'
    
    print(f"Starting server...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Templates directory: {os.path.join(BASE_DIR, 'templates')}")
    print(f"Access the application at: http://localhost:8080")
    print(f"Debug PIN: 123-456-789")  # Mostrar el PIN en la consola
    
    app.run(debug=True, host='0.0.0.0', port=8080)
