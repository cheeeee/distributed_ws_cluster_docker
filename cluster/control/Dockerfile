FROM alpine:3.7

RUN apk -U upgrade && echo http://nl.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories && \
    apk -U --no-cache add git python3 && \
    pip3 install --upgrade pip setuptools && \
    ln -s /usr/bin/python3 /usr/bin/python

RUN mkdir -p /tmp
WORKDIR /tmp
ADD . /tmp/
RUN pip3 install -r control/requirments.txt --no-cache-dir
RUN chmod 777 /tmp -R
#RUN python3 /tmp/rest-balancer.py

EXPOSE 80
