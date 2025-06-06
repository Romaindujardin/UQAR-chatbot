PROJET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${PROJET_ROOT}/apptainer_data/ollama_data" "${PROJET_ROOT}/apptainer_data/logs" 
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=11434 nohup apptainer run --nv --bind "${PROJET_ROOT}/apptainer_data/ollama_data:/root/.ollama" docker://ollama/ollama:latest > ${PROJET_ROOT}/apptainer_data/logs/ollama.log 2>&1 &
echo $! > "${PROJET_ROOT}/apptainer_data/ollama_data/ollama.pid"
echo "Ollama started. Check ${PROJET_ROOT}/apptainer_data/logs/ollama.log for logs." 