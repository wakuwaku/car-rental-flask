# start the website
start \
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \ 
python app.py &

# open the website in safari <for Mac>
open -a Safari "http://127.0.0.1:5001"
