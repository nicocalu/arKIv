cd /tmp

curl -fsSL https://ollama.com/install.sh | sh

systemctl enable ollama.service
systemctl start ollama.service

mkdir -p /etc/systemd/system/ollama.service.d
touch /etc/systemd/system/ollama.service.d/override.conf
echo '[Service]' > /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_MODELS=/tmp"' >> /etc/systemd/system/ollama.service.d/override.conf

module load python
git clone https://github.com/nicocalu/arKIv
cd arKiv
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

echo "### TRANSFER API KEY ###"