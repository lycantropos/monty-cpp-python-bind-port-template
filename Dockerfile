ARG IMAGE_NAME
ARG IMAGE_VERSION

FROM ${IMAGE_NAME}:${IMAGE_VERSION}

RUN pip install --upgrade pip setuptools

WORKDIR /opt/{{project}}

COPY requirements-setup.txt .
RUN pip install --force-reinstall -r requirements-setup.txt

COPY requirements.txt .
RUN pip install --force-reinstall -r requirements.txt

COPY requirements-tests.txt .
RUN pip install --force-reinstall -r requirements-tests.txt

COPY README.md .
COPY pytest.ini .
COPY setup.py .
COPY {{project}} {{project}}/
COPY src/ src/
COPY tests/ tests/

RUN python setup.py develop
