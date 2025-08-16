tar -czvf arKIv_backup.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='.vscode' \
    papers/ \
    metadata/ \
    vector_store.index \
    metadata.json \
    knowledge_graph.gexf