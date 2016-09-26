# coding: utf-8

from telegerrit.gerrit.listener import main
from telegerrit.settings import ssh_config


if __name__ == '__main__':
    main(ssh_config)
