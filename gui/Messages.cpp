#include "Messages.h"

#include <iostream>

Messages::Messages(QObject *parent)
    : QObject(parent)
    , notifier(fileno(stdin), QSocketNotifier::Read)
{
    connect(&notifier, &QSocketNotifier::activated, this, &Messages::onActivated);
}

void Messages::send(QString message)
{
    std::cout << message.toStdString() << std::endl;
}

void Messages::onActivated(int /*socket*/)
{
    QString s;
    s.reserve(20);

    int c;
    do
    {
        c = getchar();
        if (c != EOF)
            s.append(c);
    }
    while (c != EOF && c != '\n');

    emit received(s);
}
