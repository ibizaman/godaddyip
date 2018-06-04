# Godaddy IP

Maintains A and CNAME records matching current ip in Godaddy.

## Install
```
pip install godaddyip
```

This installs a script called `godaddyip`.

## Example use case

With the following configuration file, the daemon will maintain one A
record named `my.domain.com` to the ip of the server the daemon is
running on. It will also maintain two CNAME records
`www.my.domain.com` and `mail.my.domain.com` to `my.domain.com`.

```yaml
arecord: my
key:     mygodaddykey
secret:  mygodaddysecret
domain:  domain.com
cnames:
  - www
  - mail
```

## Configuration

Configuration files are searched in one of the following
locations. Last configuration file found takes precendence.
* `/etc/godaddyip/godaddyip.yaml`
* `~/.config/godaddyip/godaddyip.yaml`
* `./config/godaddyip.yaml`

You can override the above list of searched paths by giving the
`--config_files=path[,path,...]` argument.

Adding or removing rules to a configuration file is done by using the
`configure` argument:

```
godaddyip <config_file.yaml> arecord ARECORD
godaddyip <config_file.yaml> key KEY
godaddyip <config_file.yaml> secret SECRET
godaddyip <config_file.yaml> domain DOMAIN
godaddyip <config_file.yaml> add-cname CNAME
godaddyip <config_file.yaml> del-cname CNAME
```

## Run

Running the daemon is done by using the `run` argument:

```
godaddyip run [--config_files CONFIG_FILES]
```

Example output:
```
$ python -m godaddyip run --config_files test.yaml
Current ip: "100.99.98.97"
Previous ip: "None"
Sleeping for 5 minutes.
Current ip: "100.99.98.97"
Previous ip: "100.99.98.97"
Same ip as previous one, nothing to do
Sleeping for 5 minutes.
```

## Using systemd

The daemon can start when the system starts by creating a systemd unit
file like the following one in
`/etc/systemd/system/godaddyip.service`.

```
[Unit]
Description=Godaddy ip service
After=network.target

[Service]
User=godaddyip
Group=godaddyip
ExecStart=/usr/bin/godaddyip run
ExecReload=/bin/kill -s usr1 $MAINPID

[Install]
WantedBy=default.target
```

I advice running the daemon with a non-root user. A system user can be
created with `useradd --system godaddyip`.
