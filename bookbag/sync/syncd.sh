#! /bin/sh

case "$1" in
    start)
        twistd --python syncd.py --logfile /var/log/syncd.log --pidfile /var/run/syncd.pid
        ;;
    stop)
        kill `cat /var/run/syncd.pid`
        ;;
    restart)
        kill `cat /var/run/syncd.pid`
        twistd --python syncd.py --logfile /var/log/syncd.log --pidfile /var/run/syncd.pid
        ;;
    *)
        echo "Usage: syncd.sh {start|stop|restart}"
        exit 1
        ;;
esac

exit 0
