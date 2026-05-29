# Example Knowledge Notes

Test cases for each visualization type. Paste these into Lattice to see the corresponding renderer activate.

---

## 3D Particle Visualization

These concepts have a strong visual form and natural color — ideal for the glowing particle cloud renderer.

### Ancient Ginkgo Tree
```
The ginkgo (Ginkgo biloba) is a living fossil, unchanged for 270 million years. Its fan-shaped
leaves turn a brilliant golden yellow in autumn before dropping almost simultaneously — a phenomenon
called "peak ginkgo." The Zhangjiajie specimen is over 4,000 years old. The tree's survival through
mass extinctions is attributed to its extraordinary resilience: it regenerated near the Hiroshima
blast epicenter within a year. Its distinctive bilobed leaves produce ginkgolides, compounds with
neuroprotective properties.
```
Expected: `branching` form, `#FFD700` gold, particle cloud shaped as trunk + wide canopy.

---

### DNA Double Helix
```
DNA is a double-stranded helix wound around histone proteins. Two antiparallel strands are held
together by hydrogen bonds between complementary base pairs: adenine pairs with thymine (2 bonds),
guanine pairs with cytosine (3 bonds). The helix makes one complete turn every 10.5 base pairs,
spanning 3.4 nm. The major groove exposes base pair edges to transcription factors while the minor
groove is shallower. Supercoiling allows 2 meters of DNA to pack into a 6-micron nucleus.
```
Expected: `helical` form, `#4FC3F7` cyan-blue, dual-strand spiral.

---

### Snowflake Crystal
```
Snowflakes form when water vapor deposits directly onto ice nuclei at temperatures between -2°C and
-15°C. Each snowflake's unique hexagonal symmetry arises because all six arms experience identical
atmospheric conditions simultaneously. The dendritic branching follows fractal geometry — each branch
develops sub-branches in the same temperature-dependent pattern. At -2°C to -5°C, plates form; at
-12°C to -16°C, stellar dendrites; below -20°C, solid prisms. A single snowflake contains roughly
10^18 water molecules.
```
Expected: `crystalline` or `planar` form, `#B0E0FF` ice blue, hexagonal lattice.

---

### Mitochondria
```
Mitochondria are double-membraned organelles that generate ATP through oxidative phosphorylation.
The outer membrane is smooth and permeable to small molecules. The inner membrane is highly folded
into cristae, dramatically increasing surface area for the electron transport chain. The matrix
contains the enzymes for the Krebs cycle, mitochondrial DNA (a circular genome of 37 genes), and
ribosomes. Mitochondria divide by binary fission and are inherited maternally, suggesting they
evolved from engulfed alpha-proteobacteria 1.5 billion years ago.
```
Expected: `elongated` form, `#FF8C42` warm orange (ATP energy), inner/outer membrane structure.

---

### Milky Way Galaxy
```
The Milky Way is a barred spiral galaxy containing 200-400 billion stars, spanning 100,000 light
years across. Our solar system sits in the Orion Arm, about 26,000 light years from the galactic
center. The central bulge houses a supermassive black hole (Sagittarius A*) of 4 million solar
masses. The galactic disk rotates differentially — the inner regions rotate faster than the outer
arms. Dark matter constitutes roughly 90% of the galaxy's total mass, forming an invisible halo that
extends far beyond the visible disk.
```
Expected: `planar` form, `#C8A8F0` purple-white, spiral disc structure.

---

### Cherry Blossom (Sakura)
```
Sakura (Prunus serrulata) blooms are triggered by a chilling requirement in winter followed by
warming spring temperatures — a phenomenon called vernalization. The pale pink flowers appear before
the leaves, covering branches in dense clusters of 5-petaled blossoms. In Japan, hanami (flower
viewing) tracks the "sakura front" northward across the archipelago each spring. The blooms last
only 1-2 weeks; their brief peak is tied to the cultural concept of mono no aware — the beauty of
impermanence. Trees can live 200+ years but bloom for just 14 days annually.
```
Expected: `branching` form, `#F8C8DC` pale pink, tree-shaped canopy.

---

### Neuron
```
Neurons are electrically excitable cells that transmit signals via action potentials. A typical
neuron has a cell body (soma), multiple dendrites that receive input, and a single axon that
transmits output. The axon is insulated by myelin sheaths produced by Schwann cells, with gaps
called nodes of Ranvier that allow saltatory conduction — signals jumping between nodes at up to
120 m/s. A single neuron can form 7,000 synaptic connections. The human brain contains ~86 billion
neurons and an equal number of glial cells.
```
Expected: `branching` form, `#BA68C8` purple, dendritic tree with axon trunk.

---

## Diagram Visualization

Static, labeled diagrams for concepts with clear discrete components.

### Human Heart Anatomy
```
The heart is a four-chambered muscular pump. The right atrium receives deoxygenated blood from
the superior and inferior vena cava, passing it through the tricuspid valve into the right ventricle,
which pumps it to the lungs via the pulmonary artery. Oxygenated blood returns via the pulmonary
veins to the left atrium, passes the mitral (bicuspid) valve into the left ventricle — the most
muscular chamber — which drives it into systemic circulation through the aortic valve and aorta.
The sinoatrial node initiates each heartbeat at 60-100 bpm.
```

### Cell Membrane Structure
```
The plasma membrane is a fluid mosaic of phospholipids arranged in a bilayer, with hydrophilic
heads facing outward and hydrophobic tails sandwiched inside. Integral membrane proteins span the
bilayer as channels, pumps, or receptors. Peripheral proteins attach to the surface. Cholesterol
molecules are interspersed between phospholipids, regulating membrane fluidity — increasing it at
low temperatures and decreasing it at high temperatures. Glycoproteins and glycolipids on the outer
surface form the glycocalyx, involved in cell recognition.
```

---

## Animation Visualization

Sequential processes that unfold over time — best shown as step-by-step animated stages.

### Action Potential
```
An action potential is an all-or-nothing electrical signal. At rest, the membrane potential is
-70mV (resting potential), maintained by Na⁺/K⁺-ATPase pumps. When a stimulus exceeds threshold
(-55mV), voltage-gated Na⁺ channels open rapidly — Na⁺ rushes in and the membrane depolarizes
to +30mV (peak). Na⁺ channels then inactivate while voltage-gated K⁺ channels open — K⁺ rushes
out, repolarizing the membrane. Brief hyperpolarization to -80mV (refractory period) follows before
the pump restores resting potential. The entire event takes ~1 millisecond.
```

### CRISPR-Cas9 Gene Editing
```
CRISPR-Cas9 uses a guide RNA (gRNA) complementary to a target DNA sequence to direct the Cas9
endonuclease to a precise genomic location. The gRNA:Cas9 complex scans DNA until it finds the
target sequence adjacent to a PAM site (5'-NGG-3'). Cas9 unwinds the double helix, the gRNA
hybridizes to the complementary strand, and Cas9 makes a double-strand break. The cell repairs the
break via error-prone NHEJ (causing insertions/deletions that knock out the gene) or template-
directed HDR (inserting a desired sequence). This allows precise genome editing in living cells.
```

---

## Comparison Visualization

Before/after or normal/mutated states that benefit from side-by-side views.

### Sickle Cell vs Normal Red Blood Cell
```
Normal red blood cells are biconcave discs (~8μm diameter) that flex through capillaries and carry
oxygen efficiently via hemoglobin. In sickle cell disease, a single nucleotide mutation (GAG→GTG)
in the beta-globin gene causes glutamic acid to be replaced by valine. Under low-oxygen conditions,
mutant HbS polymerizes into rigid fibers, distorting the cell into a crescent (sickle) shape. Sickled
cells are rigid, clog capillaries causing vaso-occlusive pain crises, and are destroyed within 10-20
days (vs. 120 days for healthy RBCs), causing chronic hemolytic anemia.
```

### Prokaryotic vs Eukaryotic Cell
```
Prokaryotic cells (bacteria, archaea) lack a membrane-bound nucleus — their circular DNA floats in
the cytoplasm as a nucleoid. They have no mitochondria, ER, or Golgi; ribosomes are 70S. Many have
flagella for motility and a cell wall of peptidoglycan. Eukaryotic cells (animals, plants, fungi)
have a true nucleus with a double membrane, linear chromosomes with histones, and extensive
organelle systems: mitochondria, ER, Golgi, lysosomes. Ribosomes are 80S. Animal cells have
centrioles; plant cells have chloroplasts and a rigid cellulose cell wall.
```

---

## Timeline Visualization

Ordered sequences where the progression through steps matters.

### Krebs Cycle (Citric Acid Cycle)
```
The Krebs cycle regenerates oxaloacetate through 8 enzymatic steps in the mitochondrial matrix.
Acetyl-CoA (2C) combines with oxaloacetate (4C) to form citrate (6C) via citrate synthase.
Citrate isomerizes to isocitrate, which is oxidatively decarboxylated to alpha-ketoglutarate (5C),
releasing CO₂ and NADH. Alpha-ketoglutarate is decarboxylated to succinyl-CoA (4C), producing
another NADH and CO₂. Succinyl-CoA is converted to succinate, producing GTP. Succinate is oxidized
to fumarate (FADH₂), then hydrated to malate, then oxidized to oxaloacetate (final NADH). Net per
cycle: 3 NADH, 1 FADH₂, 1 GTP, 2 CO₂.
```

### Human Embryonic Development
```
Day 1: Fertilization — sperm fuses with oocyte, forming a zygote with 46 chromosomes. Days 2-3:
Cleavage — rapid mitotic divisions produce a morula of 16 identical cells. Day 4: Blastocyst forms
— outer trophoblast (future placenta) surrounds the inner cell mass (future embryo). Day 6-7:
Implantation into the uterine wall. Week 3: Gastrulation establishes the three germ layers —
ectoderm (skin, nervous system), mesoderm (muscle, bone, heart), endoderm (gut, lungs). Week 4:
The neural tube closes; the heart begins beating. Week 8: All major organ systems established;
embryo is now called a fetus.
```

---

## Interactive Visualization

Systems with adjustable parameters where seeing real-time change aids intuition.

### Ideal Gas Law
```
The ideal gas law PV = nRT describes the relationship between pressure (P), volume (V), amount
of gas (n, in moles), and temperature (T). At constant temperature (isothermal), pressure and
volume are inversely proportional — Boyle's Law: PV = constant. At constant pressure (isobaric),
volume increases linearly with temperature — Charles's Law. At constant volume (isochoric), pressure
increases with temperature — Gay-Lussac's Law. Real gases deviate from ideal behavior at high
pressures (molecules occupy volume) and low temperatures (intermolecular attractions become
significant), described by the van der Waals equation.
```

### Enzyme Kinetics (Michaelis-Menten)
```
Enzyme-substrate binding follows Michaelis-Menten kinetics: v = (Vmax × [S]) / (Km + [S]).
At low substrate concentrations ([S] << Km), the reaction rate increases linearly with substrate.
At high concentrations ([S] >> Km), the enzyme is saturated and rate approaches Vmax. Km (the
Michaelis constant) is the substrate concentration at half-maximal velocity — a measure of enzyme-
substrate affinity (low Km = high affinity). Competitive inhibitors increase apparent Km without
changing Vmax; non-competitive inhibitors decrease Vmax without changing Km. Temperature and pH
alter enzyme conformation and catalytic activity.
```
