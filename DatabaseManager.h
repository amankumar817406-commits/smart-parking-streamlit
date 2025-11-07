#pragma once
#include <QObject>
#include <QSqlDatabase>
#include <QString>
#include <optional>

struct UserRecord {
    QString id;        // UUID
    QString name;
    QString username;
    QString passwordHash;
    QString salt;
};

class DatabaseManager : public QObject {
    Q_OBJECT
public:
    static DatabaseManager& instance();
    bool open(const QString& dbPath = "users.db");
    bool ensureSchema();

    // Auth
    bool usernameExists(const QString& username);
    std::optional<UserRecord> getUserByUsername(const QString& username);
    bool createUser(const QString& name, const QString& username, const QString& plainPassword);

    // Utilities
    static QString hashPassword(const QString& plainPassword, const QString& salt);
    static QString generateSalt();
    static QString generateUuid();

private:
    explicit DatabaseManager(QObject* parent = nullptr);
    QSqlDatabase db_;
};
