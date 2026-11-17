# IB Mathematics Extended Essays — Grade A

Scraped from Clastify.com on 2026-05-08. All essays received Grade A.
Extraction: Introduction/Background (pages 1-5) + Conclusion/Bibliography (last 3 pages).

Total: 15 essays

---

<!-- ee_id: 67824dfa7adbeeaf5a4bb5d6 -->
<!-- source: https://www.clastify.com/ee/maths/67824dfa7adbeeaf5a4bb5d6 -->

# How can linear and non-linear differential equations be used to model the velocity and displacement of the Singapore Red Lions?

**Grade:** A  
**Session:** N24  
**Subject:** Maths  
**Total Pages:** 58  
**URL:** https://www.clastify.com/ee/maths/67824dfa7adbeeaf5a4bb5d6

## Introduction / Background (Pages 1-5)

Extended Essay Title Page:

Title:
 
Modelling the velocity and displacement of the Singapore Red Lions using

linear and non-linear differential equations
.

Research Question:
 
How can linear and non-linear differential equations be used to

model the velocity and displacement of the Singapore Red Lions?

Subject
: Group 5 Mathematics

Word Count:
 
3822
1. Table of Contents

2.
 
Introduction: ....................................................................................................... 1

3.
 
Methodology: ..................................................................................................... 1

4.1: Construction of Differential Equations: ................................................................... 1

4.2: Literature Review: ...................................................................................................... 3

4.3: Adapted Methodology: .............................................................................................. 5

4.4: Parameters:................................................................................................................. 6

4.5: Boundary Conditions:
 
................................................................................................ 7

4.
 
Obtaining the Solution to
 
v(t)
 
and
 
x(t)
 
using the Variable Separable

Method: ...................................................................................................................... 7

5.1: Obtaining the General Solution to
 
v(t):.................................................................... 7

5.
 
Obtaining the General Solution to
 
x(t): ........................................................... 9

6.
 
Modelling the first segment of motion for both
 
v(t)
 
and
 
x(t): .................... 10

9.1.1: Euler's Method:
 
..................................................................................................................
 
20

9.1.2: 4th Order Runge-Kutta Method (RK4): ...............................................................................
 
21

3. Introduction:

The Singapore Red Lions, perform free-fall displays at the National Day Parade

annually. These free-fall displays were the highlight of my National Day experience,

and I found myself interested in how the velocity and displacement of the Red Lions

could be modelled. Such a model help increase safety by enabling parachutists to

optimise the time at which the parachute is deployed and the altitude at which they

jump.

Hence, my research question is: How can linear and non-linear differential equations be used to model the velocity and displacement of the Singapore Red Lions?

4. Methodology:

4.1: Construction of Differential Equations:

According to Newton's 2nd Law, the nett-force felt of an object is given by F_net = ma, where m = mass, and a = acceleration.

## Conclusion / Reflections (Last 3 Pages)

First reflection session candidate comments:

Whilst choosing my research question, I decided to first narrow down the scope to differential equations. This was because differential equations was a topic that I understood well, but was powerful enough to allow me to model or optimize complex real-life applications. Whilst researching for real-life applications, I came across the Parachute Problem, wherein differential equations are used to model the velocity of a parachutist. This resonated with me, as since young, I have watched the Singapore Red Lions perform their famed free-fall displays annually at the National Day Parade. Additionally, using such a model, the Red Lions could optimize their jump height and parachute deployment altitude. It also occurred to me that given a function for velocity, I could also model displacement. Hence, I decided to model both the velocity and displacement of the Red Lions.

Interim reflection candidate comments:

During my research, I encountered several challenges. Firstly, I was unable to solve 2 differential equations analytically, as they were nonlinear and instead had to utilize numerical techniques. When selecting a method, I prioritized accuracy and computational efficiency, and after thorough research, selected the 4th Order Runge-Kutta Method (RK4). Subsequently, when performing Newton Polynomial interpolation on the generated points, I noticed that the polynomial did not pass through the interpolated points. I learnt it was because the polynomial's coefficients were rounded off, and hence, going forth I decided to not round off coefficients. Similarly, I observed that whilst theoretically my velocity model should be smooth, it contained sharp edges. I performed a diagnostic by checking each section of my EE, but was unable to find a mathematical error. This prompted me to consider errors in the online RK4 calculators I had used. I subsequently used the calculator to solve a differential equation with a known solution, and as hypothesized it produced an incorrect answer. Subsequently, I redid the necessary RK4 calculations using another software, and obtained a smooth model.

Final reflection - Viva voce candidate comments:

Through my research, I have gained 3 major learnings. Firstly, to clearly illustrate and distill complex concepts to readers, it is necessary to have a deep understanding of these methods and the principles behind them. Secondly, in mathematics, there is no universally best method. Each method comes with its own pros and cons, and we must select whichever method is most appropriate, keenly considering our unique use case. Thirdly, whilst easy, we must not overlook even the smallest inconsistencies, as they can help unravel major flaws in our research, and more importantly, help push the quality of our research forward - as in my case. When dealing with these inconsistencies, it is also vital to keep an open mind, as even the most unforeseen factors could have caused these errors. I also had the opportunity to explore an array of advanced mathematical concepts, such as, RK4, and learn how to use complex mathematical software that has provided me a greater appreciation for Mathematics. Ultimately, whilst this EE has proven challenging, the knowledge and lessons gained, and importantly, being able to answer my research question successfuly, has made this process equally rewarding.


---

<!-- ee_id: 66ef1d7cbe75fae88ac4271b -->
<!-- source: https://www.clastify.com/ee/maths/66ef1d7cbe75fae88ac4271b -->

# To what extent can image compression through Fourier analysis de-noise the CIFAR-10 dataset?

**Grade:** A  
**Session:** M24  
**Subject:** Maths  
**Total Pages:** 37  
**URL:** https://www.clastify.com/ee/maths/66ef1d7cbe75fae88ac4271b

## Introduction / Background (Pages 1-5)

I have had a profound interest in artificial intelligence for a long time, and I am also interested in pursuing the field at the collegiate level. Image classification in particular, has captured my attention. Image classification is a branch of artificial intelligence that is rapidly becoming an integral part of society. In the past few decades, the functionality of numerous industries has improved after the adoption of image classification tools.

Data scientists are always searching for ways to improve the efficacy of artificial intelligence. For image classification, that is done by increasing the accuracy of the classification algorithms. One method of increasing the accuracy of image classification algorithms, and the method that I will be investigating in this essay, is image compression via Fourier analysis. Image compression is the process by which insignificant details in an image are removed to reduce file size. Image noise, which refers to the random variations in brightness and color in an image, often falls under the umbrella of "insignificant details" and is thus nullified when compression occurs.

Research Question: To what extent can image compression through Fourier analysis de-noise the CIFAR-10 dataset?

I will begin this essay with an exploration of the math behind Fourier analysis. Then, I will investigate how image compression via Fourier analysis can de-noise CIFAR-10: a dataset containing 60000 images of ten objects. I will first train a convolutional neural network (CNN), a type of image classifier, using the original CIFAR-10 dataset. Then, I will train another CNN that contains the same properties but using a 10% compressed CIFAR-10 dataset instead. Then I'll do one for 20% compressed, 30% compressed, and so on up to 90% compression. The magnitude of image compression at which the accuracy of the CNN is the highest is the magnitude at which the dataset is best de-noised.

Fourier analysis is the process by which a complex waveform is represented as a series of sinusoidal functions. By performing Fourier analysis on a waveform, one can mathematically analyze the graphical output to determine the input equation. Fourier analysis is a process which enables data scientists to determine the period and amplitude of the various sine waves that constitute the complex waveform in question.

## Conclusion / Appendix (Last 3 Pages)

The appendix contains Python code used for the CNN image classification experiments, including code to compress images using FFT (Fast Fourier Transform) and evaluate classification accuracy at various compression levels (10%-90%).

Key code excerpt: numpy's fft2 function is used to apply 2D Fourier Transform to each image channel. A threshold is applied to keep only the top frequencies (by magnitude), and ifft2 reconstructs the compressed image. This process is applied across training and test sets before CNN training.


---

<!-- ee_id: 64c07c95f8603e0013d6497a -->
<!-- source: https://www.clastify.com/ee/maths/64c07c95f8603e0013d6497a -->

# How can Laplace Transformation be used to solve differential equations in Undamped Vibration and Kirchhoff's Laws of Current and Voltage?

**Grade:** A  
**Session:** M23  
**Subject:** Maths  
**Total Pages:** 36  
**URL:** https://www.clastify.com/ee/maths/64c07c95f8603e0013d6497a

## Introduction / Background (Pages 1-5)

Research Question: How can Laplace Transformation be used to solve differential equations in Undamped Vibration and Kirchhoff's Laws of Current and Voltage?

This essay investigates the application of engineering mathematics to complex equations. It looks into how the Laplace Transform works as an instance of engineering mathematics with significantly crucial approaches for undergraduate students of the engineering field. Out of all methods used in mathematics and physics, Laplace Transformation (LT) is the appropriate and frequently used one.

The LT converts any complex function into a simple algebraic equation as a benefit when other mathematical methods require more stages. This transform solves physics problems such as Kirchhoff's current and voltage law, digital signal processing, system modelling, and undamped vibration.

The Laplace transform is defined by the integral: L{f(s)} = F(s) = ∫₀^∞ f(t)e^(−st) dt, where s = σ + iω.

Using LT to solve differential equations has three steps:
1. Transform the equation into an algebraic (subsidiary) equation
2. Solve the equation in linear form
3. Use inverse LT to transfer the solution back into the time domain

The essay covers: Laplace Transform theory, application to undamped vibration (spring-mass systems), and application to Kirchhoff's voltage and current laws in series R-L-C circuits.

## Conclusion / Appendix (Last 3 Pages)

The appendix contains experimental data tables for the Kirchhoff's Laws experiment — voltage measurements (V) over time (t) from 0 to ~30 seconds, used to validate the Laplace Transform solutions against real circuit measurements.


---

<!-- ee_id: 63b7770cf8937e0013baf7f8 -->
<!-- source: https://www.clastify.com/ee/maths/63b7770cf8937e0013baf7f8 -->

# The Analysis of Approaches and Extension of a Combinatorial Geometry Problem

**Grade:** A  
**Session:** N22  
**Subject:** Maths  
**Total Pages:** 44  
**URL:** https://www.clastify.com/ee/maths/63b7770cf8937e0013baf7f8

## Introduction / Background (Pages 1-5)

Research Question: How does the mathematically optimized rabbit increase its distance against the hunter in problem 3 of the 2017 International Mathematics Olympiad?

This essay analyzes, solves, and extends problem 3 from the 2017 International Mathematical Olympiad (IMO) — statistically the most difficult problem in IMO history, with only 2 out of 615 contestants solving it correctly in 4.5 hours.

The problem: A hunter and an invisible rabbit play a game in the Euclidean plane starting at the same point. In each round: (i) the rabbit moves invisibly to a point exactly distance 1 away; (ii) a tracking device reports a point within distance 1 of the rabbit's actual position; (iii) the hunter moves to a point exactly distance 1 away. After 10^9 rounds, can the hunter always ensure the distance between her and the rabbit is at most 100?

The author's approach involves: solving the problem, comparing with gold medalist solutions, extending it with machine learning (NEAT algorithm), and exploring real-world applications (e.g., search-and-rescue, predator-prey dynamics).

Key notations: A_n = rabbit position after n rounds; B_n = hunter position after n rounds; d_n = distance between them; P_n = tracking device position.

The essay covers: initial geometric approach, proof method with generalized distance formula, comparison with Ivanov's (gold medalist) procedure, extension using a NEAT machine learning program for advanced hunter strategies.

## Conclusion / Appendix (Last 3 Pages)

The appendix contains the machine learning program code using Python/NEAT, and the NEAT configuration file. The ML model uses 3 inputs (relative positions) and 4 outputs (hunter movement directions), trained over 300 generations with a fitness threshold of 400. The program simulates 10,000 rounds of the hunter-rabbit game to evaluate strategy performance.


---

<!-- ee_id: 634441c9153d090014699e5c -->
<!-- source: https://www.clastify.com/ee/maths/634441c9153d090014699e5c -->

# To what extent do the motion of strings within stringed instruments described by Fourier Series give insight into consonance and dissonance in music theory?

**Grade:** A  
**Session:** M21  
**Subject:** Maths  
**Total Pages:** 28  
**URL:** https://www.clastify.com/ee/maths/634441c9153d090014699e5c

## Introduction / Background (Pages 1-5)

Research Question: To what extent do the motion of strings within stringed instruments described by Fourier Series give insight into consonance and dissonance in music theory?

This essay analyses the sounds produced by vibrating strings in instruments (guitar, violin, piano) through their mathematical motion — specifically via the wave equation and Fourier Series — and explores how interactions between these sounds produce consonant and dissonant tones in music theory.

The essay begins by deriving the wave equation from first principles. Given a pulse traveling along a string, the shape function f(x,t) = φ(x − ct) satisfies the wave equation. Using partial differentiation, the relationship ∂²f/∂t² = c²(∂²f/∂x²) (the wave equation) is established.

Structure:
1. Introduction
2. Deriving the Wave Equation
3. Solving the Wave Equation (Separation of Variables, boundary/initial conditions, uniqueness)
4. Manipulation of Vibrating Strings (decay of harmonics)
5. Connections to Music Theory (production of sound, consonance and dissonance)
6. Conclusion

Key mathematical tools: partial differential equations, separation of variables, Fourier Series, Sturm-Liouville theory, Parseval's theorem.

## Bibliography (Last 3 Pages)

References include: Benson (Music: A Mathematical Offering), Davis (Wave Equation in Mathematics of Wave Propagation), Young (An Introduction to Hilbert Space), Strang (Computational Science and Engineering), Visintin (Fourier Series and Music Theory, University of Trento, 2019), and others covering PDE theory, Fourier analysis, and music acoustics.


---

<!-- ee_id: 62e53e901459fa0013b212bc -->
<!-- source: https://www.clastify.com/ee/maths/62e53e901459fa0013b212bc -->

# What is modular arithmetic, and how can it be applied to solve problems in the field of number theory?

**Grade:** A  
**Session:** M21  
**Subject:** Maths  
**Total Pages:** 37  
**URL:** https://www.clastify.com/ee/maths/62e53e901459fa0013b212bc

## Introduction / Background (Pages 1-5)

Research Question: What is modular arithmetic, and how can it be applied to solve problems in the field of number theory?

This essay covers the foundational theory of modular arithmetic and demonstrates its application to 5 original number theory problems (mostly from UKMT Mathematics Challenges).

Modular arithmetic (established by Gauss in *Disquisitiones Arithmeticae*, 1801) concerns the remainders of integers when divided by a chosen modulus. The key notation: a ≡ b (mod n) means a and b have the same remainder when divided by n.

The system is sometimes called "clock arithmetic" — e.g., 9 + 4 ≡ 13 ≡ 1 (mod 12) gives the correct time on a 12-hour clock.

Topics covered:
1. Introduction to Modular Arithmetic and operational properties
2. The Chinese Remainder Theorem
3. Fermat's Little Theorem
4. Divisibility Tests (checksum applications including IBAN validation)
5. Original solutions to 5 number theory problems

The author's motivation: keen UKMT participant since age 13, modular arithmetic produces "succinct and elegant solutions" to competition problems.

## Bibliography

References include: Stewart's *Concepts of Modern Mathematics*, Graham/Knuth/Patashnik's *Concrete Mathematics*, Art of Problem Solving wiki resources on modular arithmetic and Fermat's Little Theorem, Encyclopaedia Britannica on the Chinese Remainder Theorem, Wikipedia on Fermat primality test and IBAN validation, and UKMT webinar on Modular Arithmetic (2020).


---

<!-- ee_id: 6971dd70edd90ed76c2fea44 -->
<!-- source: https://www.clastify.com/ee/maths/6971dd70edd90ed76c2fea44 -->

# How can Fourier Transform be applied to denoising audio signals?

**Grade:** A  
**Session:** N25  
**Subject:** Maths  
**Total Pages:** 49  
**URL:** https://www.clastify.com/ee/maths/6971dd70edd90ed76c2fea44

## Introduction / Background (Pages 1-5)

Research Question: How can Fourier Transform be applied to denoising audio signals?

This essay explores how the Fourier Transform is used to remove unwanted noise (particularly Gaussian white noise) from audio signals, with implementation in MATLAB using Fast Fourier Transform (FFT).

Audio signals are electrical representations of sound waves. The most common form of unwanted sound is white noise — an aperiodic sound with equal intensities across all audible frequencies (20–20,000 Hz) that disrupts audio clarity.

The Fourier Series expands a periodic signal f(t) as an infinite sum of sines and cosines: f(t) = Σ(a_n cos(nω₀t) + b_n sin(nω₀t)). The essay derives: periodicity conditions, orthogonality proofs for sin and cos, Fourier coefficients (a₀, a_n, b_n), complex form of Fourier Series, and ultimately the Fourier Transform.

Structure:
1. Introduction & Methodology
2. Audio Signal Processing (white noise, signal-to-noise ratio)
3. Fourier Series (periodicity, odd/even functions, orthogonality, deriving coefficients)
4. Conversion to Complex Form
5. Fourier Transform derivation
6. Application: FFT/IFFT, band-pass filter, audio denoising
7. Evaluation & Conclusion

## Reflections (RPPF)

The candidate initially explored Fourier Transform for instrumental harmonics analysis, but switched to audio signal denoising after supervisor feedback. MATLAB's FFT was used for the application (with AI coding assistance). The supervisor confirmed the student "learnt Fourier Transform through her own research" and "showed the ability to think critically." Key challenge: understanding the Dirac Delta function's Sifting property (pages 27-28). The student spent ~4 supervised hours on the EE.


---

<!-- ee_id: 688784ed75fd7ee6017ea5fb -->
<!-- source: https://www.clastify.com/ee/maths/688784ed75fd7ee6017ea5fb -->

# To what extent does Hamiltonian Equations and Matrix Exponential can be used to solve differential equations in Simple Harmonic Motion?

**Grade:** A  
**Session:** M25  
**Subject:** Maths  
**Total Pages:** 33  
**URL:** https://www.clastify.com/ee/maths/688784ed75fd7ee6017ea5fb

## Introduction / Background (Pages 1-5)

Research Question: To what extent can Hamiltonian Equations and the Matrix Exponential be used to solve differential equations in Simple Harmonic Motion?

This essay investigates the use of Hamiltonian equations and the matrix exponential method to solve the second-order differential equation governing Simple Harmonic Motion (SHM).

Simple Harmonic Motion satisfies: a ∝ −x (acceleration directly proportional and opposite to displacement). Standard IB approaches (variable separation, integrating factors, Euler's method) are well-established. The Hamiltonian approach recasts the problem in terms of energy and phase space, offering deeper insights.

The Hamiltonian function H(x, y) represents total energy: H(x, y) = KE + PE. Hamiltonian equations: dx/dt = ∂H/∂y and dy/dt = −∂H/∂x, where x = displacement, y = momentum.

The matrix exponential method uses Taylor series expansion to solve the system — the author discovered that the Taylor series for the SHM matrix yields trigonometric (cosine and sine) functions, ultimately giving exact values for displacement and momentum.

Structure:
1. Introduction
2. Literature Review (Hamiltonian equations, partial differentiation, matrix exponential)
3. Research Method
4. Application in SHM (phase space analysis, experimental validation)
5. Conclusion

## Reflections (RPPF)

The candidate initially planned on the Navier–Stokes equation but narrowed scope (too ambitious) to SHM via alternative methods. Key breakthrough: using Taylor series to solve the matrix exponential, noticing that the result matched trigonometric patterns, then simplifying with angular frequency from physics. The phase space diagram (displacement vs. momentum) emerged as an additional analytical tool — unique to the Hamiltonian method since it produces both displacement and momentum solutions simultaneously.


---

<!-- ee_id: 686f9acf2b926bbfeb75fc38 -->
<!-- source: https://www.clastify.com/ee/maths/686f9acf2b926bbfeb75fc38 -->

# How can Lotka-Volterra equations and Verhulst's logistic growth models be applied and compared to model the population and behavior of European rabbits (Oryctolagus cuniculus) in the UK from 1995 to 2024?

**Grade:** A  
**Session:** M25  
**Subject:** Maths  
**Total Pages:** 37  
**URL:** https://www.clastify.com/ee/maths/686f9acf2b926bbfeb75fc38

## Introduction / Background (Pages 1-5)

Research Question: How can Lotka-Volterra equations and Verhulst's logistic growth models be applied and compared to model the population and behavior of European rabbits (Oryctolagus cuniculus) in the UK from 1995 to 2024?

This essay applies and compares two population modelling approaches to European rabbits in the UK (1995–2024): Verhulst's logistic growth model (without predators) and Lotka-Volterra prey-predator systems (with foxes). The essay investigates how including a predator variable affects model accuracy.

Verhulst's logistic growth ODE: dP/dt = rP(1 − P/K), where r = intrinsic growth rate, P = population, K = carrying capacity. Solved via separation of variables and partial fractions.

Lotka-Volterra system: a system of two coupled ODEs modelling prey (rabbit) and predator (fox) populations simultaneously. Key mathematical tools: equilibrium/critical points, eigenvalues, and eigenvectors.

Structure:
1. Introduction
2. Methodology (logistic growth, Lotka-Volterra ODE systems, equilibria, eigenvalues)
3. Applying Logistic Growth to the Rabbit Population (solving unknowns, accuracy evaluation)
4. Applying Lotka-Volterra (solving unknowns, eigenvalues, accuracy evaluation)
5. Conclusion & Bibliography

## Reflections (RPPF)

The candidate's motivation was pursuing a career in computer science and ecosystem modelling. Initially focused on Lotka-Volterra only, the essay was expanded to include logistic growth models to create a meaningful comparison of predator-inclusive vs. predator-free models. Main challenge: fox population parameter data was scarce, requiring pure mathematical derivation as a workaround. The candidate mastered partial differentiation and ODE systems independently, beyond the IB syllabus.


---

<!-- ee_id: 686bc943a803c1b22f010112 -->
<!-- source: https://www.clastify.com/ee/maths/686bc943a803c1b22f010112 -->

# How can mathematical modelling that employs differential equations determine population growth patterns for a Wolf and an Elk?

**Grade:** A  
**Session:** M25  
**Subject:** Maths  
**Total Pages:** 29  
**URL:** https://www.clastify.com/ee/maths/686bc943a803c1b22f010112

## Introduction / Background (Pages 1-5)

Research Question: How can mathematical modelling that employs differential equations determine population growth patterns for a Wolf and an Elk?

This essay applies the Lotka-Volterra predator-prey model (pair of first-order nonlinear ODEs) to model wolf and elk population dynamics in Northwood Park. The candidate's interest arose from watching a PBS Nature documentary noting an unusually high elk-to-wolf ratio.

The Lotka-Volterra model (Alfred Lotka 1910, Vito Volterra 1926) uses coupled nonlinear differential equations reflecting population oscillations, equilibrium states, and predator-prey interactions. The essay goes beyond the basic model to include: Jacobian matrix stability analysis, parameter estimation via Bayesian inference, Markov Chain Monte Carlo (MCMC) simulations, and Runge-Kutta numerical methods — all implemented in Python.

Structure:
1. Introduction
2. Investigation & Planning
3. Lotka-Volterra model
4. Assumptions and limitations
5. Example calculation with Jacobian matrix
6. Parameter estimation (forward/inverse problem, Bayesian inference, MCMC)
7. Conclusion (evaluation, improvements, future extensions)

## Reflections (RPPF)

The candidate initially planned to study mountain nyala and African wild dog populations in Ethiopia but switched to wolves and elks due to data availability. Key challenges: analytical parameter estimation was "intractable" — required Python for Jacobian matrix, Runge-Kutta, Bayesian inference, and MCMC. Lognormal distributions were added to model measurement error. The candidate notes: "mathematical modeling is all about continuously refining and improving." Future extension: stochastic differential equations to account for random ecological processes.


---

<!-- ee_id: 686aa074a803c1b22fcbbcf9 -->
<!-- source: https://www.clastify.com/ee/maths/686aa074a803c1b22fcbbcf9 -->

# How do macroscopic models, specifically fundamental diagrams, and microscopic models like Webster's method and Markov chains contribute to understanding and optimizing traffic flow dynamics?

**Grade:** A  
**Session:** M25  
**Subject:** Maths  
**Total Pages:** 51  
**URL:** https://www.clastify.com/ee/maths/686aa074a803c1b22fcbbcf9

## Introduction / Background (Pages 1-5)

Research Question: How do macroscopic models, specifically fundamental diagrams, and microscopic models like Webster's method and Markov chains contribute to understanding and optimizing traffic flow dynamics?

This essay analyses macroscopic and microscopic traffic flow models — their mathematical foundations and real-world applications in traffic optimization. Context: the average London commuter wastes 156 hours/year due to congestion (INRIX).

Traffic models are classified as:
- **Macroscopic**: describe aggregate traffic behaviour (density, flux, velocity) using hydrodynamic theory. Key model: Greenshield's fundamental diagrams (1930s) — three relationships: speed-density, speed-flow, density-flow.
- **Microscopic**: simulate individual vehicle behaviour, model reactions to road infrastructure, queue formations, travel time delays. Key methods: Webster's method (traffic light optimization) and Markov chains.

Structure:
1. Introduction
2. Basic concepts of traffic flow models (macro/micro/meso)
3. Macroscopic Model (Fundamental Diagrams, Greenshield model, real-life application)
4. Microscopic Models (traffic light optimization via Webster's method; Markov chains)
5. Conclusion & Bibliography

## Reflections (RPPF)

The candidate pivoted twice: from traffic flow → aerodynamics of car bodies (fluid dynamics) → back to traffic flow. The aerodynamics route was abandoned because it required simulations and advanced maths beyond reach. The final focus on traffic flow allowed more accessible mathematical depth with broader applications. The essay combines real traffic data (speed/density/flow measurements) with theoretical models.


---

<!-- ee_id: 686a7b98a803c1b22fc4d274 -->
<!-- source: https://www.clastify.com/ee/maths/686a7b98a803c1b22fc4d274 -->

# How can a Sierpinski Triangle be constructed and traversed under the context of constrained N–disc Hanoi Tower problem?

**Grade:** A  
**Session:** M25  
**Subject:** Maths  
**Total Pages:** 32  
**URL:** https://www.clastify.com/ee/maths/686a7b98a803c1b22fc4d274

## Introduction / Background (Pages 1-5)

Research Question: How can a Sierpinski Triangle be constructed and traversed under the context of constrained N-disc Hanoi Tower problem?

This essay explores the deep mathematical connection between the Sierpinski Triangle (a self-similar fractal) and the constrained Tower of Hanoi problem — where discs may only move to adjacent rods.

The constrained Tower of Hanoi is solved using the ternary number system: moving the unit digit corresponds to moving the smallest disc; every carry in ternary corresponds to moving a larger disc. This creates a recursive structure that, when disc-configurations are connected as graph nodes, produces a graph isomorphic to the Sierpinski Triangle.

Structure:
1. Introduction (Tower of Hanoi, Sierpinski fractal, connection overview)
2. Solving the Constrained Tower of Hanoi (ternary system, carry digits)
3. Construction of Sierpinski Triangle and Implications (graph theory, proof by induction)
4. Expected Number of Random Moves (Markov chain methods, probability matrices)
5. Hausdorff Dimension of the Sierpinski Triangle
6. Further Investigation and Research Directions
7. Conclusion & Bibliography

Key mathematical tools: ternary number system, graph theory, proof by induction, Markov chains, Hausdorff dimension (fractal geometry). Python used for random move simulation and graph visualisation.

## Reflections (RPPF)

The candidate initially planned stochastic music generation via Markov chains, but pivoted (too interdisciplinary) to the Tower of Hanoi-Sierpinski connection. The insight emerged from a spontaneous realisation during a graph theory problem. Key challenge: deriving expected random moves analytically proved difficult — probability matrices and Markov chain calculations were implemented via Python instead. The essay sparked the candidate's interest in space-filling curves and higher-dimensional fractals.


---

<!-- ee_id: 666c2b4223885f531f2f47ab -->
<!-- source: https://www.clastify.com/ee/maths/666c2b4223885f531f2f47ab -->

# How can the exit velocity vector of a spacecraft performing a hyperbolic flyby manoeuvre be calculated?

**Grade:** A  
**Session:** M23  
**Subject:** Maths  
**Total Pages:** 38  
**URL:** https://www.clastify.com/ee/maths/666c2b4223885f531f2f47ab

## Introduction / Background (Pages 1-5)

Research Question: How can the exit velocity vector of a spacecraft performing a hyperbolic flyby manoeuvre be calculated?

This essay analyses the hyperbolic flyby manoeuvre (gravity assist) using vectors, trigonometry, and orbital mechanics, deriving a set of formulae to calculate exit velocity — then validating them against real Voyager 2 data from its Jupiter flyby.

Background: Gravity assists are essential to interplanetary travel (e.g., Voyager 2 used flybys of Jupiter, Saturn, Uranus, Neptune to reach ~35 km/s). The topic was inspired by BepiColombo's Mercury gravity assist.

Key definitions:
- Hyperbolic excess velocity (v∞): spacecraft velocity before/after flyby, where gravitational influence is negligible
- Heliocentric velocity: velocity relative to the Sun
- Periapsis: closest point to planet during flyby
- Sphere of influence: region where planet's gravity dominates
- Leading/trailing side flyby: whether spacecraft crosses in front of or behind the planet's orbital motion

Structure:
1. Introduction
2. Definitions, Variables, Assumptions
3. Description of the problem (hyperbolic excess velocities, heliocentric velocities, velocity change)
4. Analysis (vector components, solving for outbound velocity, finding angles, magnitude/direction)
5. Application to Voyager 2 – Jupiter flyby (real data, calculations, final considerations)
6. Conclusion & Bibliography

## Conclusion

The calculation yielded 21.29 km/s vs. the actual value — an error of ~3 km/s (11.5%). Key sources of error: 2D model (real flyby is 3D), neglected gravitational influence of Jupiter's moons and nearby Saturn, and approximate inbound heliocentric velocity angle taken from trajectory graphs. Future direction: extend to 3D analysis or model gravity assists themselves. Bibliography includes Bate & Mueller's *Fundamentals of Astrodynamics*, Curtis's *Orbital Mechanics for Engineering Students*, NASA Horizons ephemeris system, and Kluever's *Space Flight Dynamics*.


---

<!-- ee_id: 64ac374b7345620013099d36 -->
<!-- source: https://www.clastify.com/ee/maths/64ac374b7345620013099d36 -->

# How does Elliptic Curve Cryptography ensure secure communication of information on the internet?

**Grade:** A  
**Session:** M23  
**Subject:** Maths  
**Total Pages:** 29  
**URL:** https://www.clastify.com/ee/maths/64ac374b7345620013099d36

## Introduction / Background (Pages 1-5)

Research Question: How does Elliptic Curve Cryptography ensure secure communication of information on the internet?

This essay explores the mathematical foundations of Elliptic Curve Cryptography (ECC) — a public-key cryptosystem first introduced in the 1980s, now used in Bitcoin, Ethereum, and secure internet communication (TLS). Motivation: learning that elliptic curves underpin blockchain digital signatures (ECDSA) and key exchange (ECDH).

Public key cryptography uses asymmetric encryption: a public key encrypts, a private key decrypts (and vice versa for digital signing). The essay explains this through the "Alice and Bob" padlock analogy.

Structure:
1. Introduction
2. Public Key Cryptography (asymmetric encryption, digital signing)
3. Preliminaries (group/ring/field definitions, modular arithmetic, Euler's Totient function)
4. Elliptic Curve Fundamentals (definition, properties, geometric operations — point addition and doubling, singularity)
5. ECC over Prime Fields (formal definition, algebraic procedures, Elliptic Curve Discrete Logarithm Problem, ECDH key exchange, parameter examples)
6. Conclusion

Key security basis: the Elliptic Curve Discrete Logarithm Problem (ECDLP) — computing the private key from the public key is computationally infeasible even for quantum computers with current hardware.

## Bibliography

References include: Bruen & Forcinito's *Cryptography, Information Theory, and Error-Correction*, Liebeck's *A Concise Introduction to Pure Mathematics*, Shevchuk's University of Chicago REU paper on ECC, Wohlwend's MIT paper on ECC pre/post quantum, Brilliant.org resources on groups/rings/fields, and Davis's *Elliptic Curve Cryptography* (Geometer.org). Appendix shows key size comparison: ECC 256-bit ≈ RSA 3072-bit security level.


---

<!-- ee_id: 63c60f90f18f2200138bd539 -->
<!-- source: https://www.clastify.com/ee/maths/63c60f90f18f2200138bd539 -->

# To what extent, statistically, are the causal effects of parenting programs on rural Chinese toddlers' cognition different between genders?

**Grade:** A  
**Session:** N22  
**Subject:** Maths  
**Total Pages:** 47  
**URL:** https://www.clastify.com/ee/maths/63c60f90f18f2200138bd539

## Introduction / Background (Pages 1-5)

Research Question: To what extent, statistically, are the causal effects of parenting programs on rural Chinese toddlers' cognition different between genders?

This essay applies multivariate regression and hypothesis testing to a 2015 randomised controlled trial (RCT) dataset of 386 rural Chinese families across 2 provinces. Half were randomly assigned to a parenting program (treatment group); the other half were controls. The essay investigates whether the program's causal effect on toddler cognition differs by gender — motivated by China's well-documented millennia-old son preference.

Cognitive development was measured using Bayley-III, the gold-standard toddler cognitive test. Scores are standardised relative to Z-distributions (mean=0, SD=1) for within-sample comparisons.

Statistical methodology built progressively:
1. Bivariate regression model
2. Multivariate regression with controls
3. Binary categorical variables (gender G, treatment T)
4. Interaction effects (G◦T — gender-treatment heterogeneity)
5. Ordinary Least Squares (OLS) derivation via partial differentiation and matrix form
6. Gauss-Markov assumptions
7. Hypothesis testing: normality of residuals, standard error, T-statistic, p-value
8. Evaluation: Bayesian interpretation of p-values, limitations of statistical significance, imperfections of causal inference, strengths of RCTs

## Data Appendix (Last 3 Pages)

The appendix contains the full raw dataset (386 observations) used in the regression: standardised final cognition scores (C), standardised estimated cognition (Ĉ), standardised baseline cognition (C₀), gender binary (G: 0=female, 1=male), treatment status (T: 0=control, 1=treatment), and the gender-treatment interaction variable (G◦T).

---

<!-- ee_id: 6a020dc2249efe79570d9c52 -->
<!-- source: https://www.clastify.com/ee/maths/6a020dc2249efe79570d9c52 -->

# To what extent can unwanted noise be analyzed by applying a Fourier transform model?

**Grade:** A  
**Session:** N/A  
**Total Pages:** 43  
**URL:** https://www.clastify.com/ee/maths/6a020dc2249efe79570d9c52

## Research Question

*(not extracted)*

## Introduction / Background (Pages 1–5)

**Title:** Applying a Fourier transform to remove unwanted audio  
**Word Count:** 3957 | **Student code:** zzzzzz

**Table of Contents:** 1. Introduction, 2. Approach, 3. Mathematical background (3.1 Audio Signal Processing, 3.2 Fourier series), 4. Fourier Series Properties (4.1 Periodicity, 4.2 Odd/Even Functions, 4.3 Orthogonality, 4.4 Fourier Coefficients), 5. Complex Form of Fourier Series, 6. Fourier Transform (6.1 Derivation, 6.2 Dirac Delta Function, 6.3 FT of Cosine Waves, 6.4 FT of Sine Waves), 7. Application (7.1 FFT/IFFT, 7.2 Denoising Audio, 7.3 SNR), 8. Evaluation, 9. Conclusion, 10. Bibliography, 11. Appendix

**1. Introduction**

The growing number of social media platforms has led to greater diversity in audio content. Noise-cancelling technology and video-editing software both rely on the Fourier transform, which decomposes audio signals into their constituent frequencies. The research question: "To what extent can unwanted noise be analysed by applying a Fourier transform model?" guides this essay.

**2. Approach**

The essay first examines fundamentals of audio signals, then derives the mathematical model from the Fourier transform approach, explains the Fourier Series in understandable steps, and demonstrates how it can denoise audio by identifying and removing background noise using coding software.

**3.1 Audio Signal Processing**

Audio signals are electrical representations of sound waves. Noise can take many forms (rain, car horns, background noise). The most common form of unwanted sound is white noise — an aperiodic sound with equal intensity across all audible frequencies.

**3.2 Fourier Series**

The Fourier series is an expansion of a periodic signal f(t) as an infinite sum of sines and cosines. Example: f(t) = sin(t) + cos(2t) can be decomposed into constituent sinusoidal functions. The Fourier series provides the foundational understanding of the Fourier transform, which decomposes a signal into simple frequency components.

**4.1 Periodicity:** Periodic functions repeat at regular intervals, allowing complex functions to be broken into periodic sinusoids. Non-periodic functions cannot be represented by simpler periodic waves.

## Conclusion / References / RPPF (Last 3 Pages)

**Appendix (MATLAB code for frequency domain filtering):**

The appendix contains MATLAB code implementing band-pass filtering using FFT/IFFT. Key steps: apply FFT to noisy signal, create frequency-domain filter H(k) for signal frequencies 2, 4, 7 rad/s while blocking noise, apply filter, then apply IFFT to recover clean signal. Outputs include: filtered signal RMS, clean signal RMS, filtering error vs clean signal, SNR improvement in dB.

**Reflective Statement (477 words):**

The essay originated from a personal interest in music — background noise disrupts audio enjoyment, and the student sought mathematical strategies to understand noise reduction. Main challenges: (1) understanding the complexity of the Fourier Transform itself, particularly how complex audio signals can be represented as sine/cosine combinations; (2) initially focused too heavily on computation and overlooked interpretation — realised that mathematics is not only about obtaining results but also about understanding their contextual meaning. Breaking the problem into smaller foundational concepts (trigonometric identities, graph transformations) was key. The investigation improved analytical skills, critical thinking, and the ability to evaluate which mathematical concepts are relevant rather than including advanced mathematics for complexity. Key insight: struggling with complex concepts is part of developing deeper knowledge; approach challenging problems methodically rather than seeking immediate solutions. Future applications: engineering, data science — will validate underlying assumptions and simpler cases before applying advanced models, and build understanding step by step.

---

<!-- ee_id: 6a020dec249efe79570dacd4 -->
<!-- source: https://www.clastify.com/ee/maths/6a020dec249efe79570dacd4 -->

# How can the heliocentric velocity following a hyperbolic flyby be calculated from known initial conditions?

**Grade:** A  
**Session:** N/A  
**Total Pages:** 28  
**URL:** https://www.clastify.com/ee/maths/6a020dec249efe79570dacd4

## Research Question

*(not extracted)*

## Introduction / Background (Pages 1–5)

1

Extended Essay Mathematics

How can the heliocentric velocity following a hyperbolic flyby be calculated from known initial conditions?

May 2027 | Word count: 3989 | Student code: XABCX

---

2

Table of Contents: 1. INTRODUCTION, 1.1 ASSUMPTIONS, 2. MATHEMATICAL BACKGROUND, 3. CONCEPTUAL OVERVIEW, 4. MATHEMATICAL FORMULATION AND DERIVATION (4.1 Setting up the problem, 4.2 Expressing vectors and components, 4.3 Solving for outbound velocity, 4.4 Finding angles), 5. APPLICATION OF DERIVED FORMULAE (5.1 Relevant data), 6. CONCLUSION, BIBLIOGRAPHY

---

3

**1. Introduction**

Some objects move due to gravity; the study of this motion is orbital mechanics, and one of the most common or useful ideas is the flyby. According to NASA, when a spacecraft passes close to a planet, the planet's gravity affects two properties: the velocity and the direction relative to the sun, so we can define them as a velocity vector. Since the orbit is related to the sun, this essay will focus on calculating the spacecraft's heliocentric velocity vector during a hyperbolic flyby under known conditions: the planet's mass and the periapsis distance.

As this investigation develops a mathematical model to perform such a calculation, the fundamentals used will include vector components, trigonometry, and hyperbolic geometry, along with initial and key conditions such as inbound and outbound hyperbolic excess velocities, heliocentric velocity, and the angle. The derived method will be applied to a real example (Voyager 2's flyby). The outbound velocity generated is then compared with the saved value to analyse how well the model performs.

**1.1 Assumptions**

- Assumption 1: The planet's heliocentric velocity is constant (circular orbit, Kepler's second law).
- Assumption 2: The planet's velocity is perpendicular to the sun.
- Assumption 3: The planet's atmosphere doesn't have an impact on the spacecraft (no air resistance).
- Assumption 4: The planet's gravitational field is even (perfectly spherical, evenly distributed mass).
- Assumption 5: No gravitational attraction from other nearby planets or moons.
- Assumption 6: No gravitational attraction exerted on the planet by the spacecraft (point-like spacecraft).

---

4

**2. Mathematical Background**

Key definitions: Hyperbolic excess velocity (v∞ inbound/outbound), Heliocentric velocity (velocity w.r.t. sun), Periapsis (closest approach point), Inbound/outbound crossing, Sphere of influence, Escape velocity, Leading/trailing side flyby.

Variables: v∞_in (inbound hyperbolic excess velocity), v∞_out (outbound), v_planet (planet heliocentric velocity), v_hel_in / v_hel_out (spacecraft inbound/outbound heliocentric velocity), unit vectors in horizontal/vertical directions, angles between velocity vectors.

---

5

**3. Conceptual Overview**

A hyperbolic flyby is a maneuver performed by a spacecraft travelling faster than the escape velocity of the planet. The spacecraft's trajectory is modelled mathematically as a hyperbola (eccentricity > 1). During the inbound crossing, the spacecraft accelerates due to the planet's gravity well. At periapsis, velocity is maximum; during outbound crossing, it decelerates. Thus after the maneuver, the spacecraft doesn't gain speed in the planet's reference frame — but gains speed in the heliocentric frame due to the planet's own motion (gravity assist effect).

## Conclusion / References / RPPF (Last 3 Pages)

**References (page 26):**
- Elsevier. (n.d.). Hyperbolic excess velocity. ScienceDirect Topics.
- Strange, N. J., Campagnola, S., & Russell, R. P. (2010). Leveraging flybys of low mass moons to enable an Enceladus orbiter.
- Bell, Edwin V. "Voyager 2." NSSDCA, 26 Nov. 2018.
- "Voyager - Mission Status." NASA.
- "Voyager 2: In Depth." NASA, 4 Feb. 2021.
- Kluever, Craig A. Space Flight Dynamics. John Wiley & Sons Ltd.
- Curtis, Howard. Orbital Mechanics For Engineering Students (Fourth Edition). Butterworth-Heinemann, 2020.
- Bate, Roger, and Donald Mueller. Fundamentals Of Astrodynamics. Dover Books on Physics, 1971.
- Bryan, Jason. "Interplanetary Gravity Assisted Trajectory Optimizer." Cal Poly Digital Commons, 2009.
- Aiton, E. J. "Kepler's Second Law of Planetary Motion." ISIS, vol. 60, 1969, pp. 75-76.
- Park, Ryan S., et al. "The JPL Planetary and Lunar Ephemerides DE440 and DE441." The Astronomical Journal, vol. 161, no. 3, 2021.
- "Horizons System." NASA. https://ssd.jpl.nasa.gov/horizons/app.html
- "Jupiter Fact Sheet." NASA.
- "Astrodynamic Parameters." NASA.
- Elsevier. (n.d.). Heliocentric velocity — An overview. ScienceDirect.

**Reflective Statement (page 27-28, 483 words):**

The investigation arose from a brief classroom mention of gravity assists during a vectors unit. The student approached the topic despite its mathematical complexity. Key challenges included working with vectors, defining directions in orbit, and angle calculations — requiring resilience to rethink the approach multiple times. The investigation changed the student's understanding of initial conditions and modelling variables: small assumption changes significantly affect outcomes. Real mission data for Voyager 2 was measured 36 hours after flyby rather than at the exact encounter point, teaching that models are interconnected systems interpreted within the context of their assumptions. Skills developed: mathematical modelling, critical evaluation of assumptions, data interpretation under uncertainty, and revising approaches when they fail. Future applications include sensitivity analysis to test how variations in angles affect results.

---

<!-- ee_id: 6a020d80249efe79570d7503 -->
<!-- source: https://www.clastify.com/ee/maths/6a020d80249efe79570d7503 -->

# To what extent do selected socio-economic factors, through a regression model, influence toddlers' cognitive development in China?

**Grade:** A  
**Session:** N/A  
**Total Pages:** 51  
**URL:** https://www.clastify.com/ee/maths/6a020d80249efe79570d7503

## Research Question

*(not extracted)*

## Introduction / Background (Pages 1–5)

**Subtitle:** Parenting program, statistical approaches  
**Word Count:** 3950 | **Student code:** XXXXX1

**1. Introduction**

In contrast to the constant growth of urban areas in China, the rural economy periodically declines, as does education and human development. By age two, half of all rural Chinese toddlers' cognitive development is sub-average. These Early Child Development (ECD) delays are correlated with mental health indicators, education formation and wages in adulthood. Moreover, it causes lifelong, transgenerational harm to 540 million rural Chinese in social aspects and life satisfaction.

When coaching parents or caregivers to stimulate their toddler's development, parenting programs in rural China significantly alleviated ECD delays. Some studies have argued that these benefits for toddlers' cognitive abilities are directly causal rather than merely tangentially correlated. However, few studies examine whether this cause-and-effect relationship depends on other factors, e.g., the toddler's gender or older-son preference. Hence, the research question evaluates candidate models on contextual econometrics knowledge — not regression's quantitative metrics — to decide the most effective model and conduct robust hypothesis tests based on evaluation of mathematical relationships.

**2. Background**

**2.1 The parenting program:** 2 Chinese provinces randomly divided 386 rural families into treatment and control groups, easing self-selection biases. Families in treatment-focused groups received expert parenting advice and resources, whereas control groups didn't. Data collected before and after treatment included: parenting practices (punishing/playing), parents' emotional development (depression/happiness), toddler's cognitive, socio-emotional and physical development (Bayley-III).

**2.2 The cognitive test:** The Bayley-III assesses toddler behavior through specific non-conditional activities (e.g., fitting square blocks into square holes). Bayley-III normative sample approaches America's population average: N(100, 15). However, China lacks analogous norming samples, so the study standardises parameters relative to N(0, 1) for within-sample comparisons.

## Conclusion / References / RPPF (Last 3 Pages)

*(Last 3 pages rendered as empty — likely dense mathematical tables/appendices not captured by text layer)*

**Note:** This EE examines socio-economic factors influencing toddler cognitive development in rural China using regression modelling. Key variables include standardised Bayley-III cognitive scores, treatment/control group assignment, gender, and socio-economic indicators. The investigation applies multivariate regression, hypothesis testing (normality of residuals, T-statistics, p-values), and Bayesian interpretation of statistical significance to a 386-family RCT dataset.

---
