# C4 Model — Concepts, Classification & Audience Mapping

Reference for reasoning about *what* to draw before writing DSL. Source: c4model.com (Simon Brown), Structurizr docs.

## Table of contents
- [1. The mental model](#1-the-mental-model)
- [2. The abstractions (the nouns)](#2-the-abstractions-the-nouns)
- [3. The diagram levels (the zooms)](#3-the-diagram-levels-the-zooms)
- [4. Audience → level mapping](#4-audience--level-mapping)
- [5. Classifying any element (decision tree)](#5-classifying-any-element-decision-tree)
- [6. Extracting a model from a codebase](#6-extracting-a-model-from-a-codebase)
- [7. Reverse-engineering an existing diagram](#7-reverse-engineering-an-existing-diagram)
- [8. Notation conventions & review checklist](#8-notation-conventions--review-checklist)
- [9. Anti-patterns to avoid](#9-anti-patterns-to-avoid)

---

## 1. The mental model

C4 is **abstraction-first, notation-second**. Agree on *what the boxes mean* (a fixed vocabulary) before worrying about shapes/colours. Diagrams are **"maps of code"** — one underlying model viewed at different **zoom levels**, each telling a different story to a different audience. Most teams only need the top two levels.

## 2. The abstractions (the nouns)

Strict nesting: **Person → Software System → Container → Component → Code element.**

| Abstraction | Means | Examples |
|---|---|---|
| **Person** | A human user / role / actor | Customer, Admin, Support Agent |
| **Software System** | Highest unit of delivery; something that delivers value. Mark systems you don't own as *external*. | "Internet Banking System", "Stripe (external)" |
| **Container** | A **separately deployable / runnable** unit — an app or a data store. **NOT a Docker container.** | SPA, mobile app, API service, database, message broker, serverless function, cache |
| **Component** | A grouping of related functionality behind an interface, **inside** a container. Not separately deployable. | "Sign-In Controller", "Payment Service", a Spring `@Service` |
| **Code element** | Implementation detail | class, interface, function, table |

> The word **"Container" = a thing that runs** (a process/runtime boundary). It has nothing to do with containerization/Docker. This is the #1 source of confusion.

## 3. The diagram levels (the zooms)

| Level | Diagram | Shows | When to use |
|---|---|---|---|
| 1 | **System Context** | Your system as one box + its users + the external systems it talks to | Almost always; sets the scene |
| 2 | **Container** | The deployable apps & data stores inside the system, their tech + responsibilities + comms | Almost always; the workhorse |
| 3 | **Component** | Major components inside **one** container | Only for complex containers that need it |
| 4 | **Code** | UML class diagram / ERD inside one component | Rarely; auto-generate or skip |

Supplementary diagrams:
- **System Landscape** — a "map" of *multiple* systems across an enterprise/department (a System Context without a single-system focus). For portfolio/org-wide views.
- **Dynamic** — runtime collaboration for one use case (numbered interaction steps).
- **Deployment** — maps containers onto infrastructure (servers, cloud, regions). For ops.

**Official guidance:** you don't need all four levels — only those that add value. **System Context + Container are sufficient for most teams.**

## 4. Audience → level mapping

When the audience is not specified, infer it from the request; otherwise default to **developers & architects → Context + Container**.

| Audience / purpose | Generate these views | Why |
|---|---|---|
| **Executives / business / non-technical** | System Context only | What it does & who it touches; no jargon |
| **Product managers / new joiners / cross-team** | Context + Container | Shape of the system |
| **Architects** | Context + Container (+ System Landscape for portfolio) | Boundaries & integrations |
| **Developers** | Container + Component (+ Code if asked) | They build inside containers |
| **Ops / SRE / Infrastructure** | Deployment (+ Container for reference) | Where it runs |
| **"Document the whole thing" / unspecified** | Context + Container (default) | The sufficient-for-most-teams baseline |

Rule of thumb: the higher the audience sits in the org, the wider the zoom. Start at Context; zoom in only as far as the audience needs.

## 5. Classifying any element (decision tree)

Apply to every box found in code or in an existing diagram:

```
Is it a human / role / actor?              → PERSON
Is it a system you do NOT own/control?     → EXTERNAL SOFTWARE SYSTEM (tag "External")
Is it a deployable/runnable thing you own
   (app, service, DB, queue, cache, fn)?   → CONTAINER
Is it a code module/package inside a
   running thing?                          → COMPONENT
Is it a class / table / function?          → CODE element
Is it infra (server, VM, region, pod, LB)? → DEPLOYMENT node (not a static element)
```

## 6. Extracting a model from a codebase

Work top-down, gathering evidence from the repo. Choose how deep to go based on the target levels (§4).

**System Context (level 1) — find the system, its users, external integrations:**
- README / docs for purpose & users.
- Outbound HTTP clients, SDKs, env vars (`*_API_URL`, `*_API_KEY`), `package.json`/`pom.xml`/`requirements.txt` dependencies → external systems (payment, email, auth, analytics, third-party APIs).
- Auth config (OAuth providers, SSO) → external identity systems + person roles.

**Container (level 2) — find separately deployable units:**
- `docker-compose.yml`, Kubernetes/Helm manifests, `Procfile`, IaC (Terraform/Bicep/CloudFormation) → services, DBs, queues, caches.
- Monorepo layout: each app/service/package with its own entrypoint/build = a container.
- Datastores: connection strings, ORM configs, migrations → databases; broker configs (Kafka/RabbitMQ/SQS) → message brokers; Redis/Memcached → caches.
- Frontends: SPA/mobile/desktop projects = containers.
- Label each container with its **technology** (framework/language) and a one-line **responsibility**.

**Component (level 3) — drill into ONE container only when needed:**
- Packages/modules/layers: controllers, services, repositories, gateways, handlers.
- DI registrations (Spring beans, NestJS providers, ASP.NET services) → components.
- Keep it to the *major* building blocks, not every class.

**Code (level 4):** skip unless explicitly requested.

If the codebase is large, infer **natural higher-level abstractions** rather than enumerating everything — group related modules into a sensibly-named component/container. Favour intuitive, business-meaningful names over mechanical ones.

## 7. Reverse-engineering an existing diagram

When the source is an existing diagram (image, Mermaid, PlantUML, ad-hoc boxes, UML):

1. **Inventory** every box and arrow.
2. **Classify** each box with the decision tree (§5).
3. **Detect altitude** — old diagrams usually *mix levels*. Group classified boxes: persons+systems → Context; apps+datastores of one system → Container; modules inside one app → Component.
4. **Split** any single diagram that spans multiple altitudes into separate C4 diagrams — one per level. (This is the highest-value transformation.)
5. **Re-home special notations**: UML class diagram → Code; network/infra diagram → Deployment; UML sequence diagram → Dynamic.
6. **Fix relationships**: make every arrow directional, with a verb-phrase label + protocol.
7. **Add missing metadata**: technology label + one-line responsibility per element.
8. **Validate** against the checklist (§8).

Common source-notation mappings:

| Source symbol | Likely C4 mapping |
|---|---|
| Stick figure / "user" | Person |
| Cloud "3rd-party API" | External Software System |
| Box "Order Service" / "Web App" | Container |
| Cylinder (database) | Container (data store) |
| Queue / topic symbol | Container (message broker) |
| Box-inside-a-box module | Component |
| UML class | Code element |
| Server / VM / pod | Deployment node |

## 8. Notation conventions & review checklist

C4 is notation-independent, but every diagram should be self-explanatory. Validate the generated DSL/diagram against:

**General**
- [ ] Has a **title** (diagram type + scope).
- [ ] Diagram **type** is identifiable.
- [ ] **Scope** is understandable.
- [ ] Has a **key/legend** (the playground auto-generates one from styles).

**Elements**
- [ ] Every element's **type** is clear (Person/System/Container/Component).
- [ ] Every element has a short **responsibility description**.
- [ ] Every container/component has an explicit **technology** label.

**Relationships**
- [ ] Every line is **directional** and **labelled** with intent (+ protocol where useful). No naked arrows.

## 9. Anti-patterns to avoid

1. **Mixing abstraction levels** in one diagram — keep each diagram at one altitude.
2. **Confusing "Container" with Docker** — it means *deployable unit*.
3. **Unlabelled / bidirectional arrows.**
4. **Missing legend / title / technology labels.**
5. **Over-diagramming** — producing Component/Code diagrams nobody asked for. Context + Container is enough for most teams.
6. **Hand-maintained Code-level diagrams** — they rot; skip or auto-generate.
7. **Notation bikeshedding** before the abstractions are agreed.
