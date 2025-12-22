# Rapid Ribosome Profiling (UMI-enabled library prep)

## Summary
### Description
Ribosome profiling (Ribo-seq) measures translation by sequencing ribosome-protected RNA fragments, allowing you to infer where ribosomes sit on transcripts genome-wide. This workflow aims to keep the wet-lab portion relatively fast while retaining the key steps needed for quantitative analysis, including unique molecular identifiers (UMIs) to reduce PCR-duplication bias.

### Before Start
Read the full workflow once end-to-end, then confirm you have the appropriate kits and consumables for your chosen size-selection and depletion options.

## Materials
| Oligo/adapter | Sequence |
| --- | --- |
| RiboS_linker | rCAAGCAGAAGACGGCATACGAGAT |
| RiboS_linker_primer | ATCTCGTATGCCGTCTTCTGCTTG |
| RiboS_IlluminaAdapt_TSO_UMI_RNA_F | ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNGATrGrGrG |
| RiboS_blocking_oligo | CTACCCCAAGCAG |
| Read 1 sequencing primer (Illumina; standard) | ACACTCTTTCCCTACACGACGCTCTTCCGATCT |
| Index 1 Read | GATCGGAAGAGCACACGTCTGAACTCCAGTCAC[i7]ATCTCGTATGCCGTCTTCTGCTTG |
| Index 2 Read | AATGATACGGCGACCACCGAGATCTACAC[i5]ACACTCTTTCCCTACACGACGCTCTTCCGATCT |

### Additional reagents (cultured mammalian lysis/footprinting; Step 1 sub-steps)
| Reagent | Notes |
| --- | --- |
| PBS | Use ice-cold PBS for the wash step. |
| Harringtonine (optional) | If doing initiation profiling, apply immediately before lysis per your lab standard. |
| DMSO (optional) | Solvent for harringtonine stock preparation. |
| Cycloheximide | Included in polysome buffer to stall elongation. |
| Triton X-100 | Detergent for lysis buffer. |
| Turbo DNase I | Added to lysis buffer to reduce viscosity from genomic DNA. |
| Sucrose | For the 1 M sucrose cushion. |
| RNase I | Used to digest exposed RNA and generate footprints (100 U/μl stock). |
| SUPERase·In RNase inhibitor | Used to quench RNase I digestion and included in cushion. |
| miRNeasy RNA isolation kit | Used for RNA extraction from the ribosome pellet. |
| Qiazol reagent | Used to resuspend the ribosome pellet (from miRNeasy kit). |
| GlycoBlue | Coprecipitant to improve RNA recovery. |
| 3 M sodium acetate (pH 5.5) | Precipitation salt. |
| Isopropanol | Precipitation solvent. |
| RNase-free water | For buffer prep and resuspension. |

### Buffer recipes (cultured mammalian lysis/footprinting)
| Buffer | Composition / preparation |
| --- | --- |
| Polysome buffer | 20 mM Tris·Cl (pH 7.4), 150 mM NaCl, 5 mM MgCl2, 1 mM DTT and 100 μg ml−1 cycloheximide (prepare fresh; keep on ice). |
| Lysis buffer | Polysome buffer + 1% (vol/vol) Triton X-100 + 25 U ml−1 Turbo DNase I (prepare fresh with RNase-free reagents). |
| Sucrose cushion (1 M) | Polysome buffer + 1 M sucrose (∼34% (wt/vol) sucrose; 10 ml is 3.4 g sucrose dissolved in 7.8 ml polysome buffer) + 20 U ml−1 SUPERase·In (prepare fresh with RNase-free reagents). |
| Tris (10 mM, pH 8) | Prepare with RNase-free reagents; store at room temperature (22–25 °C). |

Other materials (examples; equivalents are acceptable):
- Column-based RNA cleanup kit (e.g., Monarch RNA Cleanup Kit, 10 µg scale).
- RNA/cDNA cleanup magnetic beads (e.g., RNAClean XP / AMPure XP class beads).
- RtcB RNA ligase.
- RNase inhibitor (e.g., SUPERase·In class).
- Template-switching RT enzyme mix.
- Optional size-selection supplies: urea PAGE materials, TBE, agarose gel supplies.

## Equipment (cultured mammalian lysis/footprinting; Step 1 sub-steps)
| Equipment | Notes |
| --- | --- |
| Cell lifter / scraper | For harvesting adherent cells directly in the dish. |
| Needle (26 G) and 1 ml syringe | For trituration to reduce clumps. |
| Nonstick RNase-free Microfuge tubes | For lysate handling and RNA work. |
| Polycarbonate ultracentrifuge tube (13 mm × 51 mm) | Tube for sucrose cushion spin. |
| Ultracentrifuge + rotor | TLA100.3-class rotor capable of 70,000 r.p.m. |
| Refrigerated microcentrifuge | For clarification and RNA pelleting at 4 °C. |
| Nutator / rotator | For gentle mixing during digestion. |
| Liquid nitrogen and dry ice (optional) | For flash-freezing lysis option. |

## Steps
### RNA isolation and nuclease footprinting

#### Step 1

Perform RNA isolation and ribosome footprint generation in a way that fits your biological system.

For adherent cultured mammalian cells, you can use the following sub-steps (Step 1-1 through Step 1-17):

**Cell lysis (Timing: ~30 min)**

Critical: If performing initiation site profiling with harringtonine, apply the drug immediately before lysis and proceed without delays.

#### Step 1-1

Remove media from one 10-cm dish of adherent cells. Move the dish onto ice, rinse with 5 ml ice-cold PBS, and remove the PBS completely.

#### Step 1-2

Lyse cells directly in the dish either immediately (option A) or after rapid freezing (option B). Flash-freezing can help preserve *in vivo* ribosome positions if harvesting is slow or stressful, though expression-level measurements are often similar in standard cultured cells.

- Option A (no freezing): Add 400 μl ice-cold lysis buffer to fully cover the dish surface.
- Option B (flash-freeze): Briefly immerse in liquid nitrogen, transfer to dry ice, add 400 μl ice-cold lysis buffer onto the frozen dish, then thaw on wet ice in the presence of lysis buffer.

#### Step 1-3

Tilt the dish so lysis buffer pools at one edge. Scrape cells into the pooled buffer, then pipette the buffer back across the surface and scrape again to maximize recovery.

#### Step 1-4

Transfer the lysate to a Microfuge tube kept on ice. Pipette up/down several times to disperse clumps, then incubate for 10 min on ice.

#### Step 1-5

Shear the lysate by passing it through a 26-G needle ten times.

#### Step 1-6

Clarify the lysate by centrifuging for 10 min at 20,000*g* and 4 °C, then collect the cleared supernatant.

**Nuclease footprinting and ribosome recovery (Timing: ~6 h)**

#### Step 1-7

Aliquot 300 μl clarified lysate (from Step 1-6), add 7.5 μl RNase I (2 U/µl), and digest for 45 min at room temperature with gentle mixing (e.g., a Nutator).

#### Step 1-8

Quench the digestion by adding 10.0 μl SUPERase·In RNase inhibitor.

#### Step 1-9

Move the digestion mix into a 13 mm × 51 mm polycarbonate ultracentrifuge tube. Underlay 0.90 ml of 1 M sucrose cushion by placing the tip at the bottom of the tube and dispensing slowly. The lysate should remain layered above the cushion with a clear interface.

#### Step 1-10

Pellet ribosomes through the cushion by ultracentrifugation in a TLA100.3 rotor at 70,000 r.p.m. and 4 °C for 4 h.

#### Step 1-11

Before removing the tube from the rotor, mark the outside edge where the pellet is expected. Carefully remove the supernatant by pipetting. The ribosome pellet can be glassy/translucent and may become apparent only after the liquid is removed.

#### Step 1-12

Resuspend the ribosome pellet in 700 μl Qiazol reagent (miRNeasy kit).

#### Step 1-13

Extract RNA from the Qiazol suspension using the miRNeasy kit protocol for total RNA including small RNAs. Elute into a nonstick RNase-free tube.

Critical: From this point onward, treat all samples as RNase-sensitive: use fresh gloves, RNase-free reagents, and RNase-free tubes/tips.

#### Step 1-14

Precipitate RNA by adding 38.5 μl water, 1.5 μl GlycoBlue, and 10.0 μl 3 M sodium acetate (pH 5.5), then add 150 μl isopropanol.

#### Step 1-15

Incubate the precipitation for at least 30 min on dry ice.

Pause point: You can extend this precipitation overnight on dry ice or at −80 °C.

#### Step 1-16

Pellet RNA by centrifuging for 30 min at 20,000*g* and 4 °C. Remove all liquid carefully, then air-dry the pellet (tube on its side) for 10 min.

#### Step 1-17

Resuspend RNA in 5.0 μl of 10 mM Tris (pH 8).

Pause point: Store RNA overnight at −20 °C or long-term at −80 °C.

### Optional: short-fragment enrichment

#### Step 2

Optional (recommended): enrich for short RNA fragments using either denaturing (urea) PAGE or a bead + membrane-based selection workflow.

#### Step 3

Combine 10 µL RNA, 30 µL RNA XP beads, and 10 µL 100% isopropanol.

#### Step 3

Add an appropriate volume of 2× RNA loading buffer to each RNA sample.

#### Step 3.1
- Duration: 300 s (5 min)
- Is Substep: True

Incubate at Room temperature for 300 s (5 min)
Place on a magnetic rack.
Transfer the supernatant to a clean 1.5 ml tube.

#### Step 4
- Duration: 180 s (3 min)

Heat-denature at 80 °C for 60 s (1 min), then chill on ice for ≥120 s (2 min).

#### Step 4

Add 100 µL RNA Cleanup Binding Buffer

#### Step 5

Load samples onto the polyacrylamide gel using TBE running buffer.

#### Step 5

Add 300 µL absolute ethanol and mix by pipetting.

#### Step 6

Place an RNA cleanup column in its collection tube, load the sample, and close the cap.

### Denaturing PAGE run

#### Step 6

Pre-run the gel in 1× TBE at 100 V for 10 min.

### Optional: short-fragment enrichment

#### Step 6.1
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 7
- Duration: 5400 s (1 h 30 min)

Run electrophoresis for 5400 s (1 h 30 min) at 100 V.

#### Step 7

Return the column to the collection tube.

#### Step 7.1
- Is Substep: True

Add 500 µL RNA Cleanup Wash Buffer.

#### Step 7.2
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 7.3
- Is Substep: True

Repeat for a total of two washes.

#### Step 8
- Duration: 180 s (3 min)

Stain the gel for 180 s (3 min) in 1× SYBR Gold prepared in 1× TBE, with gentle shaking.

#### Step 8

Move the column to a clean 1.5 ml microfuge tube.

#### Step 9

Image the gel and excise the desired band/region (20–40 nt).

#### Step 9

Add 10 µL nuclease-free water directly onto the membrane and incubate at room temperature for 300 s (5 min).

#### Step 10

Transfer the excised gel slice to a 1.5 mL microcentrifuge tube and weigh it.

#### Step 10

Centrifuge for 60 s (1 min).

#### Step 10.1
- Is Substep: True

Tip: Crushing the gel slice in the tube can improve RNA recovery.

#### Step 11

Add 4 volumes of Monarch RNA Cleanup Binding Buffer to the tube containing the gel slice.

### Notes

#### Step 11

### Optional: short-fragment enrichment

#### Step 12
- Duration: 600 s (10 min)

Incubate at 55 °C, mixing occasionally, until the gel slice fully dissolves (typically <600 s (10 min)).

### Linker ligation

#### Step 12

Add 1 µL of 100 micromolar (µM) `RiboS_linker` to 10 µL RNA. Heat at 70 °C for 60 s (1 min), then cool to room temperature.

### Optional: short-fragment enrichment

#### Step 13

Add 2 volumes of absolute ethanol to the sample and mix thoroughly by pipetting.

### Linker ligation

#### Step 13

Set up the ligation reaction below and incubate for 5400 s (1 h 30 min) at 37 °C
| Component | Volume (μl) |
| --- | --- |
| RNA and linker | 11 |
| RtcB Reaction Buffer (10X) | 2 |
| SUPERase·In (20 U/μl) | 1 |
| 1 mM GTP | 2 |
| 10 mM MnCl2 | 2 |
| RtcB RNA Ligase | 1.5 |
| H2O | 0 |

### Optional: short-fragment enrichment

#### Step 14
- Duration: 300 s (5 min)

Continue incubation at 55 °C for an additional 300 s (5 min).

### RNA cleanup

#### Step 14

Add 100 µL RNA Cleanup Binding Buffer.

### Optional: short-fragment enrichment

#### Step 15

Place an RNA cleanup column in a collection tube, load the sample, and close the cap.

### RNA cleanup

#### Step 15

Add 150 µL absolute ethanol and mix by pipetting.

### Optional: short-fragment enrichment

#### Step 15.1
- Duration: 60 s (1 min)
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 16

Return the column to the collection tube.

### RNA cleanup

#### Step 16

Place an RNA cleanup column in a collection tube, load the sample, and close the cap.

### Optional: short-fragment enrichment

#### Step 16.1
- Is Substep: True

Add 500 µL RNA Cleanup Wash Buffer.

### RNA cleanup

#### Step 16.1
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

### Optional: short-fragment enrichment

#### Step 16.2
- Duration: 60 s (1 min)
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 16.3
- Is Substep: True

Repeat for a total of two washes.

#### Step 17

Move the column to a clean 1.5 ml microfuge tube.

### RNA cleanup

#### Step 17

Return the column to the collection tube.

#### Step 17.1
- Is Substep: True

Add 500 µL RNA Cleanup Wash Buffer.

#### Step 17.2
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 17.3
- Is Substep: True

Repeat for a total of two washes.

### Optional: short-fragment enrichment

#### Step 18
- Duration: 300 s (5 min)

Add 10 µL nuclease-free water directly onto the membrane and incubate at room temperature for 300 s (5 min).

### RNA cleanup

#### Step 18

Move the column to a clean 1.5 ml microfuge tube.

### Optional: short-fragment enrichment

#### Step 19
- Duration: 60 s (1 min)

Centrifuge for 60 s (1 min).

### RNA cleanup

#### Step 19

Add 10 µL nuclease-free water directly onto the membrane and incubate at room temperature for 300 s (5 min).

### Notes

#### Step 20

### RNA cleanup

#### Step 20

Centrifuge for 60 s (1 min).

### Linker ligation

#### Step 21
- Duration: 60 s (1 min)

Add 1 µL of 100 micromolar (µM) `RiboS_linker` to 10 µL RNA. Heat at 70 °C for 60 s (1 min), then cool to room temperature.

### RT (TSO) reaction

#### Step 21

| Component | Volume (μl) |
| --- | --- |
| RNA | 9 |
| RiboS_linker_primer (100uM; reverse transcription primer) | 2 |
| dNTP mix (10 mM each) | 2 |
Mix thoroughly by pipetting at least 10 times, then briefly centrifuge to bring liquid to the bottom.
Denature for 300 s (5 min) at 70 °C in a thermal cycler, then place on ice for ≥60 s (1 min).

### Linker ligation

#### Step 22
- Duration: 5400 s (1 h 30 min)

Assemble the ligation mix below and incubate for 5400 s (1 h 30 min) at 37 °C.
| Component | Volume (μl) |
| --- | --- |
| RNA and linker | 11 |
| RtcB Reaction Buffer (10X) | 2 |
| SUPERase·In (20 U/μl) | 1 |
| 1 mM GTP | 2 |
| 10 mM MnCl2 | 2 |
| RtcB RNA Ligase | 1.5 |
| H2O | 0 |

### RT (TSO) reaction

#### Step 22

Briefly vortex the Template Switching RT Buffer, then quick-spin.
Combine the following components in a reaction tube:
| Component | Volume (μl) |
| --- | --- |
| Template Switching RT Buffer | 5 |
| RiboS_IlluminaAdapt_TSO_UMI_RNA_F (75uM) | 1 |
| Template Switching RT Enzyme Mix | 1 |
Mix by pipetting at least 10 times, then briefly centrifuge to bring liquid to the bottom.

### RNA cleanup

#### Step 23

Add 100 µL RNA Cleanup Binding Buffer.

### RT (TSO) reaction

#### Step 23

Combine 7 µL RT reaction mix (above) with 13 µL of the annealed mix. Mix by pipetting ≥10 times, then briefly centrifuge.
Incubate using the program below:
| Temperature (°C) | Time (min) |
| --- | --- |
| 42 | 90 |
| 85 | 5 |
| 4 | 1 |

### RNA cleanup

#### Step 24

Add 150 µL absolute ethanol and mix by pipetting.

### Index PCR

#### Step 24

| Component | Volume (μl) |
| --- | --- |
| 10 µM Forward Index Primer |   2.5   |
| 10 µM Reverse Index Primer |   2.5   |
| RiboS_blocking_oligo   |   2   |
| 2X Phusion Master Mix   |   25   |
| TSO reaction |   18   |
| Cycles | Temp (C) | Time (s) |
| --- | --- | --- |
| 1 | 98 | 30 |
| 10 | 98 | 5 |
|  | 60 | 5 |
| 1 | 72 | 10 |
Fragment is 150bp excluding insert at this stage
AATGATACGGCGACCACCGAGATCTACAC[i5]ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNGATGGG[INSERT]CAAGCAGAAGACGGCATACGAGAT[i7]GTGACTGGAGTTCAGACGTGTGCTCTTCCGATC

### RNA cleanup

#### Step 25

Place an RNA cleanup column in a collection tube, load the sample, and close the cap.

### Index PCR

#### Step 25

Add 90 µL AMPure XP beads to the PCR product.
Incubate at room temperature for 300 s (5 min).
Place on a magnetic rack.
Remove and discard the supernatant.
Wash with 200 µL 50% (v/v) ethanol, wait 30 s, then remove the ethanol.
Repeat the 70% ethanol wash once more.
Resuspend beads in 10 µL of H2O.
Incubate for 120 s (2 min).
Transfer the eluate to a clean PCR tube.

### RNA cleanup

#### Step 25.1
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 26

Return the column to the collection tube.

### Optional: Agarose gel size selection

#### Step 26

Run a 1% agarose gel, excise the desired band, and perform a gel cleanup using your standard method.

### RNA cleanup

#### Step 26.1
- Is Substep: True

Add 500 µL RNA Cleanup Wash Buffer.

#### Step 26.2
- Is Substep: True

Centrifuge for 60 s (1 min), then discard the flow-through.

#### Step 26.3
- Is Substep: True

Repeat for a total of two washes.

#### Step 27

Move the column to a clean 1.5 ml microfuge tube.

### Optional: Depletion of Abundant Sequences by Hybridization

#### Step 27

Optional: deplete abundant unwanted sequences (e.g., rRNA) using a hybridization-based depletion method such as DASH, following your lab’s established protocol.

### RNA cleanup

#### Step 28

Add 10 µL nuclease-free water directly onto the membrane and incubate at room temperature for 300 s (5 min).

### Quantification

#### Step 28

Assess library size on a TapeStation/Bioanalyzer.
Quantify by Qubit or qPCR using a library quantification kit, then pool samples according to your sequencing depth targets.

### RNA cleanup

#### Step 29

Centrifuge for 60 s (1 min).

### RT (TSO) reaction

#### Step 30
- Duration: 360 s (6 min)

| Component | Volume (μl) |
| --- | --- |
| RNA | 9 |
| RiboS_linker_primer (100uM; reverse transcription primer) | 2 |
| dNTP mix (10 mM each) | 2 |
Mix by pipetting ≥10 times, then briefly centrifuge to bring liquid to the bottom.
Denature for 300 s (5 min) at 70 °C in a thermal cycler, then place on ice for ≥60 s (1 min).

#### Step 31

Briefly vortex the Template Switching RT Buffer, then quick-spin.
Combine the following components in a reaction tube:
| Component | Volume (μl) |
| --- | --- |
| Template Switching RT Buffer | 5 |
| RiboS_IlluminaAdapt_TSO_UMI_RNA_F (75uM) | 1 |
| Template Switching RT Enzyme Mix | 1 |
Mix by pipetting ≥10 times, then briefly centrifuge to bring liquid to the bottom.

#### Step 32

Combine 7 µL RT reaction mix (above) with 13 µL of the annealed mix. Mix by pipetting ≥10 times, then briefly centrifuge.
Incubate using the program below:
| Temperature (°C) | Time (min) |
| --- | --- |
| 42 | 90 |
| 85 | 5 |
| 4 | 1 |

### Index PCR

#### Step 33

| Component | Volume (μl) |
| --- | --- |
| 10 µM Forward Index Primer |   2.5   |
| 10 µM Reverse Index Primer |   2.5   |
| RiboS_blocking_oligo   |   2   |
| 2X Phusion Master Mix   |   25   |
| TSO reaction |   18   |
| Cycles | Temp (°C) | Time (s) |
| --- | --- | --- |
| 1 | 98 | 30 |
| 10 | 98 | 5 |
|  | 60 | 5 |
| 1 | 72 | 10 |
Expected product: ~150 bp excluding insert at this stage.
AATGATACGGCGACCACCGAGATCTACAC[i5]ACACTCTTTCCCTACACGACGCTCTTCCGATCTNNNGATGGG[INSERT]CAAGCAGAAGACGGCATACGAGAT[i7]GTGACTGGAGTTCAGACGTGTGCTCTTCCGATC

#### Step 34
- Duration: 480 s (8 min)

Add 90 µL AMPure XP beads to the PCR product.
Incubate at room temperature for 300 s (5 min).
Place on a magnetic rack.
Remove and discard the supernatant.
Wash with 200 µL 50% (v/v) ethanol, wait 30 s, then remove the ethanol.
Repeat the 70% ethanol wash once more.
Resuspend beads in 10 µL of H2O.
Incubate for 120 s (2 min).
Transfer the eluate to a clean PCR tube.

### Optional: Agarose gel size selection

#### Step 35

Run a 1% agarose gel, excise the desired band, and perform a gel cleanup using your standard method.

### Optional: Depletion of Abundant Sequences by Hybridization

#### Step 36

Optional: deplete abundant unwanted sequences (e.g., rRNA) using a hybridization-based depletion method such as DASH, following your lab’s established protocol.

### Quantification

#### Step 37

Assess library size on a TapeStation/Bioanalyzer.
Quantify by Qubit or qPCR using a library quantification kit, then pool samples according to your sequencing depth targets.
Sequencing primer: use the standard Illumina Read 1 sequencing primer (sequence in Materials table). Read 1 begins with the UMI (`NNN`) followed by the constant `GATGGG` prefix and then the insert.

### Analysis

#### Step 38

Analyze with a standard Ribo-seq pipeline, adding UMI-aware deduplication/counting (e.g., `umi_tools`) to estimate unique molecules.
