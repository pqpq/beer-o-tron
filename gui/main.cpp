#include "Messages.h"

#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QCommandLineParser>
#include <QCursor>


int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);

    QCommandLineParser parser;
    parser.setApplicationDescription("Mash-o-matiC GUI");
    parser.addHelpOption();
    parser.addOptions({
        {"w", "Run windowed rather than full screen"}
    });

    QGuiApplication app(argc, argv);

    parser.process(app);
    if (!parser.unknownOptionNames().isEmpty())
    {
        parser.showHelp();
        return -1;
    }
    const bool isWindowed = parser.isSet("w");

    qmlRegisterType<Messages>("Beer", 1, 0, "Messages");

    QQmlApplicationEngine engine;

    QQmlContext *context = engine.rootContext();
    context->setContextProperty("runWindowed", isWindowed);

    if (!isWindowed)
    {
        QGuiApplication::setOverrideCursor(QCursor(Qt::BlankCursor));
    }

    engine.load(QUrl(QStringLiteral("qrc:/main.qml")));
    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
