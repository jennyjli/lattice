# Lattice Notebook Examples

## Getting Started

Below are example concepts that work great with Lattice. Copy any of these into the editor and click "Generate Explanation" to see the system in action.

## Oncology Examples

### Paclitaxel Mechanism

```
Paclitaxel stabilizes microtubules by preventing their depolymerization, which inhibits the mitotic spindle and prevents cancer cell division.
```

**Expected Output:** Animation showing mitosis stages and how paclitaxel blocks spindle disassembly.

### Clear Cell Carcinoma

```
Clear cell ovarian carcinoma cells look transparent because glycogen dissolves during H&E staining, leaving vacuolated cytoplasm.
```

**Expected Output:** Comparison visualization of normal vs. affected cells with glycogen dissolution steps.

---

## Chemistry Examples

### Krebs Cycle

```
The Krebs cycle oxidizes acetyl-CoA to produce NADH and FADH2, which donate electrons to the electron transport chain for ATP synthesis.
```

**Expected Output:** Animated cycle showing energy capture and transformation.

---

## Neuroscience Examples

### Synaptic Plasticity

```
Synaptic plasticity occurs through long-term potentiation when calcium influx triggers AMPA receptor insertion, strengthening the synapse.
```

**Expected Output:** Molecular-level animation of receptor trafficking and synaptic strengthening.

---

## Biology Examples

### Photosynthesis

```
Photosynthesis converts light energy into chemical energy through light-dependent and light-independent reactions in the chloroplast.
```

**Expected Output:** Diagram or animation showing light capture and ATP production.

---

## Tips for Best Results

- **Be specific:** Include mechanism names, molecules, or processes
- **Include relationships:** Mention what affects what
- **Focus on difficulty:** Describe the hard-to-visualize aspects
- **Domain keywords:** Mention the field (oncology, chemistry, biology, etc.)

## Testing the Pipeline

Run the test script to validate all examples:

```bash
python3 test_pipeline.py
```

This will:
1. Send requests to all example concepts
2. Show analysis, planning, and rendering results
3. Validate SVG generation
4. Check visualization type matching
