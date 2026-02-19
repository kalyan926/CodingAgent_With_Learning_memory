

# **Agent Execution Workflow**

---

# **1️⃣ Normal Flow — When Everything Goes Well**

## **Step 1: Goal Intake**

* User provides the **goal** or **Product Requirement Document (PRD)**.

## **Step 2: Planning**

* Reason thoroughly about the task.
* Plan a **complete sequence of todos**.
* Prepare execution order.

---

## **Step 3: Execution Cycle**

### **Initialize**

* `Next todo` → *(initially get first todo)*

---

### **Todo 1**

* Execute **Todo1**
* **Memorize**

  * Reflect on the process.
  * Store any important insights if discovered.

---

### **Todo 2**

* `Next todo`
* **Recollect**

  * Before execution, retrieve relevant memory for Todo2 context.
* Execute **Todo2**
* **Memorize**

  * Reflect and store important findings.

---

### **Todo 3**

* `Next todo`
* **Recollect**
* Execute **Todo3**
* **Memorize**

---

### **Todo 4**

* `Next todo`
* **Recollect**
* Execute **Todo4**
* **Memorize**

---

### **Continue Pattern**

Repeat:

```
Next todo
Recollect
Execute
Memorize
```

Until the **last todo is completed**.

---

## **Final Step**

* **Consolidate**

  * Consolidate short-term memory findings into long-term memory.
* **End**

---

# **2️⃣ Failure / Stuck Flow — When Progress Stops**

## **Step 1: Goal Intake**

* User provides the **goal** or **PRD**.

## **Step 2: Planning**

* Reason and plan a sequence of todos.
* Execute one by one.

---

## **Step 3: Execution Cycle with Recovery**

### **Initialize**

* `Next todo` → *(initial get first todo)*

---

### **Todo 1**

* Execute **Todo1**
* **Memorize**

  * Reflect and store important findings.

---

### **Todo 2**

* `Next todo`
* **Recollect**
* Execute **Todo2**

If stuck or error occurs:

* **Get_human_feedback**
* **Memorize**

  * Reflect on feedback and store insights.
* Retry solving with feedback.
* If still stuck → Ask again for feedback.

---

### **Resume Normal Pattern After Recovery**

* `Next todo`
* **Recollect**
* Execute
* **Memorize**

---

### **Example Extended Flow**

#### Todo3

* Recollect
* Execute
* Memorize

#### Todo4

* Recollect
* Execute

If stuck:

* Get_human_feedback
* Memorize
* Retry until successful

#### Todo5

* Recollect
* Execute
* Memorize

---

### **Continue Pattern**

Repeat:

```
Next todo
Recollect
Execute
If stuck:
    Get_human_feedback
    Memorize
    Retry
Else:
    Memorize
```

Until **last todo is completed**.

---

## **Final Step**

* **Consolidate**

  * Consolidate short-term memory into long-term memory.
* **End**

---


