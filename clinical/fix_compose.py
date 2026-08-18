"""Fix docker-compose.yml environment variables for clinical service."""
import paramiko

host = "2.24.203.81"
user = "root"
password = "Kairosopenclaw@2026"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password)

# Read the file
stdin, stdout, stderr = client.exec_command("cat /root/kairos-intelligence/docker-compose.yml")
content = stdout.read().decode('utf-8')

# Fix the empty env vars in the clinical service block
content = content.replace(
    "      - POSTGRES_USER=\n"
    "      - POSTGRES_PASSWORD=\n"
    "      - POSTGRES_DB=\n"
    "      - POSTGRES_HOST=kairos-postgres\n"
    "      - NEO4J_URI=bolt://kairos-neo4j:7687\n"
    "      - NEO4J_PASSWORD=\n"
    "      - CHROMA_HOST=kairos-chromadb\n"
    "      - CHROMA_PORT=8000\n"
    "      - CHROMA_AUTH_TOKEN=\n"
    "      - GEMINI_API_KEY=\n"
    "      - GOOGLE_API_KEY=\n",

    "      - POSTGRES_USER=${POSTGRES_USER}\n"
    "      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}\n"
    "      - POSTGRES_DB=${POSTGRES_DB}\n"
    "      - POSTGRES_HOST=kairos-postgres\n"
    "      - NEO4J_URI=bolt://kairos-neo4j:7687\n"
    "      - NEO4J_PASSWORD=${NEO4J_PASSWORD}\n"
    "      - CHROMA_HOST=kairos-chromadb\n"
    "      - CHROMA_PORT=8000\n"
    "      - CHROMA_AUTH_TOKEN=${CHROMA_AUTH_TOKEN}\n"
    "      - GEMINI_API_KEY=${GEMINI_API_KEY}\n"
    "      - GOOGLE_API_KEY=${GEMINI_API_KEY}\n"
)

# Also fix the Traefik Host label that lost the variable
content = content.replace(
    "Host(clinical.)",
    "Host(`clinical.${TRAEFIK_HOST}`)"
)

# Write back
transport = paramiko.Transport((host, 22))
transport.connect(username=user, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)
with sftp.open("/root/kairos-intelligence/docker-compose.yml", "w") as f:
    f.write(content)
sftp.close()
transport.close()

# Validate
stdin, stdout, stderr = client.exec_command("cd /root/kairos-intelligence && docker compose config --quiet && echo VALID || echo INVALID")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

client.close()
print("Done!")
