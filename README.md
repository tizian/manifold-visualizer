# 2D Specular Manifold Visualizer

![Header](https://github.com/tizian/manifold-visualizer/raw/master/docs/header.gif)

## Introduction

This is a helper tool written while working on the 2020 SIGGRAPH paper ["Specular Manifold Sampling for Rendering High-Frequency Caustics and Glints"](http://rgl.epfl.ch/publications/Zeltner2020Specular) by [Tizian Zeltner](https://tizianzeltner.com), [Iliyan Georgiev](https://www.iliyan.com), and [Wenzel Jakob](http://rgl.epfl.ch/people/wjakob). Its main use is visualize some of the ideas behind the *specular manifold constraint framework* in a simplified 2D setting, e.g. to prototype new ideas or to generate animations.

It also includes visualizations for previous work
* ["Manifold Exploration"](http://rgl.epfl.ch/publications/Jakob2012Manifold), Jakob and Marschner 2012
* ["Manifold Next Event Estimation"](https://jo.dreggn.org/home/2015_mnee.pdf), Hanika et al. 2015

The implementation is written in a combination of C++ (for ray tracing against primitives such as Bezier curves), and Python (for the main algorithms and the GUI).

## Usage

### Basics

<img src="https://github.com/tizian/manifold-visualizer/raw/master/docs/basics.jpg" alt="basics">

* The first two parts of the GUI allow you to choose between different test scenes (left), and the current *mode* (right).
* There is also a button to reload the current scene (keyboard shortcut: <kbd>R</kbd>).
* The selected scene can be moved with <kbd>Shift</kbd>+<kbd>Left mouse click+drag</kbd> and zoomed in/out with <kbd>Scroll wheel</kbd>
* Please have a look at `python/scenes.py` to define more scenes.
* You can also switch between the available three modes using the number keys <kbd>1</kbd>, <kbd>2</kbd>, and <kbd>3</kbd>.

### Raytracing

<img src="https://github.com/tizian/manifold-visualizer/raw/master/docs/raytracing.jpg" alt="raytracing">

In the *Raytracing* mode, there is one movable point for the beginning of the light path. Its position can be moved along the surface with <kbd>Left mouse click+drag</kbd> and the ray direction can be rotated with <kbd>Alt</kbd>+<kbd>Left mouse click+drag</kbd>.

**Options:**

- Toggle normals and tangents for ray intersections on specular surfaces.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/tangent_frame.jpg" alt="">


### Manifold exploration

<img src="https://github.com/tizian/manifold-visualizer/raw/master/docs/manifold_exploration.jpg" alt="manifold_exploration">

In the *Manifold exploration* mode, there is a movable point that corresponds to the end of the light path. Moving it (<kbd>Left mouse click+drag</kbd>) will attempt to perform a *manifold walk* that moves the complete light path while **a)** keeping the start point fixed, and **b)** keeping all specular contraints along the path fulfilled.
Switch to the *Raytracing* mode in order to move the start of the path instead.

**Options**:

- Toggle normals and tangents for ray intersections on specular surfaces.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/tangent_frame.jpg" alt="">

- Switch between the original specular constraints (left) based on projected half-vectors (Jakob and Marschner 2012) or the new constraints (right) based on angle differences (Zeltner et al. 2020).
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/constraint_type.jpg" alt="">

- Instead of doing full *manifold walks*, just move the specular vertices up to a first-order approximation (left toggle) and visualize the updated light path after projecting it back onto the specular manifold (right toggle). This is useful to visualize the first iteration of the underlying Newton solver.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/tangent_step.jpg" alt="">

- Set the max. number of iterations (N) and the threshold value (eps) to determine the success of the underlying Newton solver.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/newton_parameters.jpg" alt="">

### Specular manifold sampling (SMS) and manifold next event estimation (MNEE)

<img src="https://github.com/tizian/manifold-visualizer/raw/master/docs/specular_manifold_sampling.jpg" alt="specular_manifold_sampling">

In the *Specular manifold sampling* mode, there are three movable (<kbd>Left mouse click+drag</kbd>) points: the two endpoints of the path, and a position on a specular surface. The algorithm will try to refine the *initial path* derived from their configuration into a valid light path using a Newton solver.

**Options**:

- Toggle between *Manifold next event estimation* (left toggle) or *Specular manifold sampling* (right toggle).
- Set the number of specular bounces (N) that are required to sample a full path. This will usually be set appropriately based on the selected scene.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/sms_vs_mnee.jpg" alt="">

- Switch between the original specular constraints (left) based on projected half-vectors (Jakob and Marschner 2012) or the new constraints (right) based on angle differences (Zeltner et al. 2020).
- Toggle if the constraints should be visualized ("show"), and if the alternative set of constraints should be shown for the case of angle differences.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/constraint_type_2.jpg" alt="">

- Set the max. number of iterations (N) and the threshold value (eps) to determine the success of the underlying Newton solver.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/newton_parameters.jpg" alt="">

- Toggle if the paths at intermediate steps of the Newton solver should be shown. They will use a color scheme from start/red -> end/green.
- Set a scale factor for all Newton solver steps.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/intermediate_steps.jpg" alt="">

- "Go" will sample a set of "N" random points on the specular surface that will be converted to initial paths that are given to the Newton solver.
- "Show seeds" will toggle whether the initial paths should also be shown alongside the converged paths.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/sample_paths.jpg" alt="">

- "Go" will sample a set of "N" *offset microfacet normals* with a given variance (value in parentheses) for the current path that will then be used as the surface normals for the specular constraints. (See *offset manifold walks* in Jakob and Marschner 2012 and *two-stage sampling* in Zeltner et al. 2020.
<img width="400" src="https://github.com/tizian/manifold-visualizer/raw/master/docs/sample_paths_offset.jpg" alt="">


## Building

Clone the repository *recursively* with all dependencies and use CMake to generate project files for your favourite IDE or build system. Unix example using make:

```
git clone https://github.com/tizian/manifold-visualizer --recursive
cd manifold-visualizer
mkdir build
cd build
cmake ..
make
```

This will compile the C++ components of this project into a Python libray also build the [nanogui](https://github.com/mitsuba-renderer/nanogui) dependency at the same time.

## Running

Simply run the Python file in `/python/viewer.py`, but make sure both the `manifolds` and `nanogui` Python libraries are somewhere on the `PYTHONPATH`, e.g.:

```
export PYTHONPATH=<path_to_project>/build:<path_to_project>/build/ext/nanogui:$PYTHONPATH
python <path_to_project>/python/viewer.py
```

## Third party code

This project depends on the following libraries:

* [enoki](https://github.com/mitsuba-renderer/enoki)
* [nanogui](https://github.com/mitsuba-renderer/nanogui)
* [pybind11](https://github.com/pybind/pybind11)
* [tinyformat](https://github.com/c42f/tinyformat)
