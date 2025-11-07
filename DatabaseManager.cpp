#include "DatabaseManager.h"
#include <QSqlError>
#include <QSqlQuery>
#include <QVariant>
#include <QCryptographicHash>
#include <QUuid>

DatabaseManager& DatabaseManager::instance() {
    static DatabaseManager inst;
    return inst;
}

DatabaseManager::DatabaseManager(QObject* parent) : QObject(parent) {}

bool DatabaseManager::open(const QString& dbPath) {
    if (QSqlDatabase::contains("users_conn")) {
        db_ = QSqlDatabase::database("users_conn");
    } else {
        db_ = QSqlDatabase::addDatabase("QSQLITE", "users_conn");
        db_.setDatabaseName(dbPath);
    }
    return db_.open();
}

bool DatabaseManager::ensureSchema() {
    QSqlQuery q(db_);
    const char* sql =
        "CREATE TABLE IF NOT EXISTS users ("
        " id TEXT PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " username TEXT UNIQUE NOT NULL,"
        " password_hash TEXT NOT NULL,"
        " salt TEXT NOT NULL,"
        " created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ");";
    if (!q.exec(sql)) return false;

    // Ensure admin exists: username=admin, password=1234
    if (!usernameExists("admin")) {
        createUser("Administrator", "admin", "1234");
    }
    return true;
}

bool DatabaseManager::usernameExists(const QString& username) {
    QSqlQuery q(db_);
    q.prepare("SELECT 1 FROM users WHERE username = :u LIMIT 1");
    q.bindValue(":u", username);
    if (!q.exec()) return false;
    return q.next();
}

std::optional<UserRecord> DatabaseManager::getUserByUsername(const QString& username) {
    QSqlQuery q(db_);
    q.prepare("SELECT id,name,username,password_hash,salt FROM users WHERE username = :u LIMIT 1");
    q.bindValue(":u", username);
    if (!q.exec() || !q.next()) return std::nullopt;
    UserRecord r;
    r.id = q.value(0).toString();
    r.name = q.value(1).toString();
    r.username = q.value(2).toString();
    r.passwordHash = q.value(3).toString();
    r.salt = q.value(4).toString();
    return r;
}

bool DatabaseManager::createUser(const QString& name, const QString& username, const QString& plainPassword) {
    if (username.isEmpty() || plainPassword.isEmpty() || name.isEmpty()) return false;
    if (usernameExists(username)) return false;

    const QString salt = generateSalt();
    const QString hash = hashPassword(plainPassword, salt);
    const QString uuid = generateUuid();

    QSqlQuery q(db_);
    q.prepare("INSERT INTO users (id,name,username,password_hash,salt) VALUES (:id,:n,:u,:h,:s)");
    q.bindValue(":id", uuid);
    q.bindValue(":n", name);
    q.bindValue(":u", username);
    q.bindValue(":h", hash);
    q.bindValue(":s", salt);
    return q.exec();
}

QString DatabaseManager::hashPassword(const QString& plainPassword, const QString& salt) {
    QByteArray data = (plainPassword + salt).toUtf8();
    QByteArray digest = QCryptographicHash::hash(data, QCryptographicHash::Sha256);
    return QString::fromLatin1(digest.toHex());
}

QString DatabaseManager::generateSalt() {
    return QUuid::createUuid().toString(QUuid::WithoutBraces);
}

QString DatabaseManager::generateUuid() {
    return QUuid::createUuid().toString(QUuid::WithoutBraces);
}
