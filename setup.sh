cd /tmp

curl -fsSL https://ollama.com/install.sh | sh

systemctl enable ollama.service
systemctl start ollama.service

mkdir -p /etc/systemd/system/ollama.service.d
touch /etc/systemd/system/ollama.service.d/override.conf
echo '[Service]' > /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_MODELS=/tmp"' >> /etc/systemd/system/ollama.service.d/override.conf


git clone https://github.com/nicocalu/arKIv
cd arKIv

chmod +x run.sh

module load python
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

echo "### REBOOT AND TRANSFER API KEY ###"
echo "#   python -m venv venv           #"
echo "#   source venv/bin/activate      #"
