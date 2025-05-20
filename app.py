from flask import Flask, render_template, request, redirect, url_for
import random

app = Flask(__name__)

# In-memory data store for tools and requests
TOOLS = [
    {'id': 1, 'name': 'Hammer', 'description': 'Steel hammer', 'available': True},
    {'id': 2, 'name': 'Drill', 'description': 'Cordless drill', 'available': True},
    {'id': 3, 'name': 'Lawn Mower', 'description': 'Electric lawn mower', 'available': True},
]

RENTAL_REQUESTS = []

@app.route('/')
def index():
    return render_template('index.html', tools=TOOLS)

@app.route('/request/<int:tool_id>', methods=['GET', 'POST'])
def request_tool(tool_id):
    tool = next((t for t in TOOLS if t['id'] == tool_id), None)
    if not tool:
        return 'Tool not found', 404

    if request.method == 'POST':
        renter = request.form.get('renter')
        days = int(request.form.get('days', '1'))
        price = random.randint(5, 20) * days
        RENTAL_REQUESTS.append({
            'tool': tool,
            'renter': renter,
            'days': days,
            'price': price,
        })
        return render_template('confirmation.html', tool=tool, renter=renter, days=days, price=price)
    return render_template('request.html', tool=tool)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
