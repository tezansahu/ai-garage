# Structurizr DSL Reference

Condensed, practical reference for writing valid Structurizr DSL. Source: docs.structurizr.com (basics, identifiers, archetypes, expressions, language). Use this when authoring the `.dsl` file.

## Table of contents
- [1. File structure & syntax rules](#1-file-structure--syntax-rules)
- [2. Model elements](#2-model-elements)
- [3. Identifiers](#3-identifiers)
- [4. Relationships](#4-relationships)
- [5. Views](#5-views)
- [6. Styling](#6-styling)
- [7. Deployment](#7-deployment)
- [8. Expressions (include/exclude filtering)](#8-expressions-includeexclude-filtering)
- [9. Archetypes (reduce duplication)](#9-archetypes-reduce-duplication)
- [10. Complete worked examples](#10-complete-worked-examples)
- [11. Gotchas & common errors](#11-gotchas--common-errors)

---

## 1. File structure & syntax rules

A workspace has two main blocks: `model` (elements + relationships) and `views` (diagrams).

```
workspace "Name" "Description" {
    model {
        // elements and relationships
    }
    views {
        // diagrams + styles
    }
}
```

Rules (from `dsl/basics`):
- **Processed sequentially** — forward referencing is NOT supported. Define elements before referencing them.
- **Case-insensitive keywords** — `softwareSystem` == `softwaresystem`.
- **Quotes**: optional for single-word values; required when a value contains spaces. Use `""` to skip an optional positional property.
- **Braces**: opening `{` must be on the same line as the statement; closing `}` on its own line.
- **Indentation** amount is irrelevant; token separation matters.
- **Uniqueness**: person/software-system names must be globally unique; container names unique within a system; component names unique within a container.

Comments:
```
/* multi-line */
# single line
// single line
```

Constants/variables:
```
!const NAME value
!var NAME value
// reference with ${NAME}
```

---

## 2. Model elements

```
person <name> [description] [tags] { ... }
softwareSystem <name> [description] [tags] { ... }
container <name> [description] [technology] [tags] { ... }
component <name> [description] [technology] [tags] { ... }
group <name> { ... }            // visual grouping; contains ONE element type
```

Nesting (the C4 hierarchy):
- `person` and `softwareSystem` live in `model` (or a `group`).
- `container` lives inside a `softwareSystem`.
- `component` lives inside a `container`.

Child properties available inside any element block: `description`, `technology` (container/component only), `tags`, `url`, `properties { k v }`, `perspectives`, `relationships`.

```
ss = softwareSystem "Internet Banking System" "Lets customers view accounts" {
    web = container "Web Application" "Delivers static content + SPA" "Java, Spring MVC"
    spa = container "Single-Page App" "Banking functionality in the browser" "JavaScript, React"
    api = container "API Application" "Banking functionality via JSON/HTTPS" "Java, Spring Boot"
    db  = container "Database" "Stores accounts, transactions" "PostgreSQL" {
        tags "Database"
    }
}
```

External systems/people: just create them normally and tag them, e.g. `tags "External"`, then style that tag grey.

---

## 3. Identifiers

Assign an identifier (variable) to reference an element later. Valid chars: `a-zA-Z_0-9`.

```
p  = person "User"
ss = softwareSystem "Software System"
p -> ss "Uses"
rel = p -> ss "Uses"     // relationships can have identifiers too
```

Scoping:
- **Flat (default)**: all identifiers are global; names cannot be reused.
- **Hierarchical**: add `!identifiers hierarchical` at the top of the workspace. Then nested elements are referenced with dot notation and identifiers can repeat across parents.

```
workspace {
    !identifiers hierarchical
    model {
        ss1 = softwareSystem "System 1" { api = container "API" }
        ss2 = softwareSystem "System 2" { api = container "API" }
        // reference as ss1.api and ss2.api
    }
}
```
(Hierarchical scoping does NOT apply to groups.)

---

## 4. Relationships

```
<source> -> <destination> [description] [technology] [tags] { ... }
```

```
u   -> ss        "Uses"
web -> api       "Makes API calls to" "JSON/HTTPS"
api -> db        "Reads from and writes to" "JDBC"
```

- Relationships are **directional**; always add a description (verb phrase). Add technology/protocol as the next argument.
- `this` refers to the element currently in scope (useful inside an element block).
- Remove with `-/>` (in deployment views).
- **Implied relationships**: a relationship between two nested elements implies relationships between their parents. Toggle with `!impliedRelationships <true|false>` at workspace level.

---

## 5. Views

Each view needs a unique **key** (string) for stable layout. Each view body lists `include`/`exclude` and optional `autoLayout`.

```
views {
    systemLandscape "Landscape" {            // whole enterprise; no single-system focus
        include *
        autoLayout
    }
    systemContext <ssId> "Context" {         // one system + its users + external systems
        include *
        autoLayout
    }
    container <ssId> "Containers" {           // the containers inside one system
        include *
        autoLayout
    }
    component <containerId> "Components" {     // the components inside one container
        include *
        autoLayout
    }
    dynamic <*|ssId|containerId> "Flow" {      // runtime collaboration, numbered steps
        u -> web "Logs in"
        web -> api "Validates credentials"
        autoLayout
    }
    deployment <*|ssId> <environmentName> "Prod" {  // maps containers to infrastructure
        include *
        autoLayout
    }
    filtered <baseKey> <include|exclude> <tags> "Key" { }
    custom "Key" "Title" { }                   // only custom `element`s
    image <*|elementId> "Key" { }              // embed external png/plantuml/mermaid
}
```

`autoLayout [tb|bt|lr|rl] [rankSep] [nodeSep]` — direction defaults to `tb` (top-bottom). **Always include `autoLayout`** so the playground positions elements without manual layout.

`include *` — wildcard, includes everything relevant for the view's scope. Use `include`/`exclude` with [expressions](#8-expressions-includeexclude-filtering) to refine.

`title "..."` overrides the view title; `description "..."` sets the subtitle.

---

## 6. Styling

Styling lives inside `views { styles { ... } }`. Match an element/relationship by **tag**.

```
styles {
    element "Element" {
        shape roundedbox
        background #1168bd
        color #ffffff
    }
    element "Person" {
        shape person
        background #08427b
        color #ffffff
    }
    element "Database" {
        shape cylinder
    }
    element "External" {
        background #999999
        color #ffffff
    }
    element "Container" {
        background #438dd5
        color #ffffff
    }
    relationship "Relationship" {
        thickness 2
        color #707070
        style dashed          // solid | dashed | dotted
        routing Orthogonal    // Direct | Orthogonal | Curved
    }
}
```

Shapes: `Box, RoundedBox, Circle, Ellipse, Hexagon, Diamond, Cylinder, Bucket, Pipe, Person, Robot, Folder, WebBrowser, Window, Terminal, Shell, MobileDevicePortrait, MobileDeviceLandscape, Component`.

Element style props: `shape, icon, width, height, background, color/colour, stroke, strokeWidth (1-10), fontSize, border (solid|dashed|dotted), opacity (0-100), metadata (true|false), description (true|false)`.

Built-in default tags you can target: `Element`, `Person`, `Software System`, `Container`, `Component`, plus any custom tag you add via `tags "..."`.

Instead of hand-styling, a quick clean look: `themes default` (or `theme <url>`), which applies the official Structurizr theme.

**Legibility:** small, text-heavy boxes capture blurry. Make boxes roomy and text large, e.g.:
```
element "Element" { width 550 height 350 fontSize 26 shape roundedbox }
relationship "Relationship" { fontSize 24 }
```
Pair this with terse element descriptions and ≲15–18 boxes per view (see SKILL.md "Legibility"). Crowded diagrams cannot be made readable by styling alone — raise the abstraction or split the view.

---

## 7. Deployment

For the **Deployment** diagram (ops/infrastructure audience). Define an environment, nest deployment nodes, and place container/system instances inside.

```
model {
    // ... softwareSystem ss with containers web, api, db ...
    deploymentEnvironment "Production" {
        deploymentNode "Customer's computer" "" "Windows/macOS" {
            deploymentNode "Web Browser" "" "Chrome, Edge" {
                containerInstance spa
            }
        }
        deploymentNode "Amazon Web Services" "" "AWS" {
            region = deploymentNode "us-east-1" {
                deploymentNode "Autoscaling group" {
                    deploymentNode "Amazon EC2" {
                        containerInstance api
                    }
                }
                deploymentNode "Amazon RDS" {
                    containerInstance db
                }
            }
        }
    }
}
```
- `deploymentNode <name> [description] [technology] [tags] [instances] { ... }` — can nest.
- `containerInstance <containerId>` / `softwareSystemInstance <ssId>` / `instanceOf <id>` — place a running instance.
- `infrastructureNode <name>` — load balancers, firewalls, DNS, etc.
- `instances "4"` or ranges like `"1..N"`.

---

## 8. Expressions (include/exclude filtering)

Use inside views to filter what appears. Quote expressions containing whitespace.

Type & attribute filters:
```
include "element.type==Container"
include "element.tag==Database"
exclude "element.tag==External"
include "element.parent==api"
include "element.technology==PostgreSQL"
```

Coupling / relationship filters:
```
include ->api->          // api plus everything directly connected to it
include *->db            // all relationships into db
exclude "* -> *"         // remove all relationships
include "relationship.tag==Async"
```

Combine with `&&` / `||`:
```
include "element.type==Container && element.tag!=External"
```

---

## 9. Archetypes (reduce duplication)

Define a custom type once, reuse it. Great for "all my containers are Spring Boot apps".

```
model {
    archetypes {
        springApp = container {
            technology "Java, Spring Boot"
            tag "Application"
        }
        datastore = container {
            technology "PostgreSQL"
            tag "Database"
        }
        https = -> {
            technology "HTTPS"
        }
    }
    ss = softwareSystem "Banking" {
        api = springApp "API Application"
        db  = datastore "Database"
        api -> db "Reads/writes"
    }
    user = person "Customer"
    user --https-> ss "Uses"
}
```
Element archetypes can extend `person, softwareSystem, container, component, deploymentNode, infrastructureNode, group, element`. Archetypes can inherit from other archetypes.

---

## 10. Complete worked examples

### A. Minimal Context + Container (the default for most requests)

```
workspace "Internet Banking" "C4 model for the internet banking system" {

    model {
        customer = person "Personal Banking Customer" "A customer of the bank"

        banking = softwareSystem "Internet Banking System" "Lets customers view accounts and make payments" {
            spa = container "Single-Page Application" "Provides banking features in the browser" "JavaScript, React"
            web = container "Web Application" "Delivers the SPA and static content" "Java, Spring MVC"
            api = container "API Application" "Provides banking functionality via a JSON/HTTPS API" "Java, Spring Boot"
            db  = container "Database" "Stores user accounts, transactions, audit logs" "PostgreSQL" {
                tags "Database"
            }
        }

        mainframe = softwareSystem "Mainframe Banking System" "Core banking system of record" {
            tags "External"
        }
        email = softwareSystem "E-mail System" "Microsoft Exchange" {
            tags "External"
        }

        customer -> banking "Views accounts and makes payments using"
        customer -> web "Visits bank.com using" "HTTPS"
        web -> spa "Delivers to the customer's browser"
        spa -> api "Makes API calls to" "JSON/HTTPS"
        api -> db "Reads from and writes to" "JDBC"
        api -> mainframe "Makes API calls to" "XML/HTTPS"
        api -> email "Sends e-mail using" "SMTP"
        email -> customer "Sends e-mails to"
    }

    views {
        systemContext banking "SystemContext" {
            include *
            autoLayout
        }
        container banking "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Element"  { shape roundedbox width 550 height 350 fontSize 26 color #ffffff }
            element "Person"   { shape person background #08427b }
            element "Software System" { background #1168bd }
            element "Container" { background #438dd5 }
            element "Database" { shape cylinder }
            element "External" { background #999999 }
            relationship "Relationship" { thickness 2 fontSize 24 routing Orthogonal }
        }
    }
}
```

### B. Adding a Component view (drill into one container)

```
        // inside the api container block, declare components:
        api = container "API Application" "..." "Java, Spring Boot" {
            signin   = component "Sign In Controller" "Handles authentication" "Spring MVC Controller"
            accounts = component "Accounts Controller" "Account info endpoints" "Spring MVC Controller"
            security = component "Security Component" "Hashes/validates credentials" "Spring Bean"
            dbfacade = component "Database Facade" "Data access" "Spring Bean"
        }
        // relationships between components and to the db:
        signin -> security "Uses"
        accounts -> dbfacade "Uses"
        dbfacade -> db "Reads from and writes to" "JDBC"
```
```
    views {
        component api "Components" {
            include *
            autoLayout
        }
    }
```

---

## 11. Gotchas & common errors

- **Forward reference**: referencing an identifier before it is declared → "element does not exist". Declare first.
- **Missing identifier in a view**: `systemContext <id>` / `container <id>` / `component <id>` requires the *identifier* of the system/container, not its name string.
- **Duplicate names**: two software systems or people with the same name → error. Use distinct names or hierarchical identifiers.
- **`technology` on the wrong element**: only containers/components/deployment nodes take a technology argument; a `softwareSystem` does not.
- **Braces on wrong line**: `{` must end the statement line; a `{` on its own line errors.
- **A view with no `autoLayout`** renders but elements may stack at the origin in the playground — always add `autoLayout`.
- **Component view of a container that has no components**: declare components inside the container first.
- **Group can mix types**: a `group` may only contain one element type (all people, or all systems, or all containers).
- **Unquoted multi-word value**: `container Web Application` errors; quote it: `container "Web Application"`.
