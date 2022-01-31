# Client readme

To be able to run flask commands, you need to set ENV var first:

```bash
export FLASK_APP=run.py
```

# Migrations

## To generate migrations diff run:

```bash
flask db migrate
```

## To apply migrations run:

```bash
flask db upgrade
```

# Package creation

## Archlinux

```bash
cd archlinux
makepkg
```

## Debian

```bash
python3 setup.py --command-packages=stdeb.command bdist_deb
```
