// Update admin user with FULL password hash for "admin123"
db.users.deleteMany({ username: "admin" });
db.users.insertOne({
    username: "admin",
    email: "admin@nexi.lab",
    full_name: "System Administrator",
    role: "admin",
    databases_scope: ["*"],
    is_active: true,
    password_hash: "$2b$12$pEN.ZL6TjeDvqi1Nhy3GVuYm0tcjZazctPN9KjDsf5mNfOoP/c2mlm",
    created_at: new Date()
});
print("Admin user recreated with full hash. Password: admin123");
