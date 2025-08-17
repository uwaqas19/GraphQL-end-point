# Sample GraphQL Queries

### 1. Compute Box Volume
```graphql
query {
  boxVolume(dx: 2, dy: 3, dz: 4)
}
```

### 2. Compute Surface Area
```graphql
query {
  surfaceArea(dx: 5, dy: 10)
}
```

### 3. Detect Clashes (IFC)
```graphql
query {
  detectClashes(filePath: "sample_ifc/sample.ifc")
}
```

### 4. Login (JWT)
```graphql
mutation {
  login(username: "admin", password: "password")
}
```
