#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


function migrate {
    cd /code/p0sx
    python manage.py migrate
}

function shell {
    cd /code/p0sx
    python manage.py shell_plus
}


function prod {
    echo Starting uwsgi.
    exec uwsgi --chdir=/code/p0sx \
        --module=p0sx.wsgi:application \
        --master --pidfile=/tmp/project-master.pid \
        --socket=0.0.0.0:8080 \
        --http=0.0.0.0:8081 \
        --processes=5 \
        --harakiri=20 \
        --max-requests=5000 \
        --offload-threads=4 \
        --static-map=/static=/code/collected_static \
        --static-map=/media=/code/media \
	--log-master \
        --vacuum
}

function devserver {
    cd /code/p0sx
    python manage.py runserver_plus 0.0.0.0:8000
}

"$@"
