#ifndef MESSAGES_H
#define MESSAGES_H

#include <QObject>
#include <QSocketNotifier>

class Messages : public QObject
{
    Q_OBJECT
public:
    explicit Messages(QObject *parent = nullptr);

    Q_INVOKABLE void send(QString message);
    Q_SIGNAL void received(QString message);

private:
    void onActivated(int socket);
    QSocketNotifier notifier;
};

#endif // MESSAGES_H
