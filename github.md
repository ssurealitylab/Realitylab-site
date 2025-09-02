---
layout: page
title: GitHub Repositories
---

{% include sidl-script.html %}

<style>
.portfolio-item {
  margin-bottom: 30px;
}
.portfolio-link {
  position: relative;
  display: block;
  max-width: 100%;
  margin: 0 auto;
  cursor: pointer;
  text-decoration: none;
}
.portfolio-hover {
  background: rgba(254, 209, 54, 0.9);
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: all ease 0.5s;
}
.portfolio-link:hover .portfolio-hover {
  opacity: 1;
}
.portfolio-hover-content {
  position: absolute;
  width: 100%;
  height: 20px;
  font-size: 20px;
  text-align: center;
  top: 50%;
  margin-top: -12px;
  color: white;
}
.portfolio-link {
  transform: scale(1);
  transition: transform 0.3s ease;
}
.portfolio-link:hover {
  transform: scale(1.05);
}
.portfolio-caption {
  max-width: 400px;
  margin: 0 auto;
  background-color: white;
  text-align: center;
  padding: 25px;
}
.portfolio-caption h4 {
  text-transform: uppercase;
  margin: 0;
  color: #212529;
}
.portfolio-caption p {
  font-style: italic;
  font-size: 16px;
  margin: 0;
  color: #6c757d;
}
.repo-img {
  width: 100%;
  height: 250px;
  object-fit: cover;
  border-radius: 5px;
}
</style>

<!-- GitHub Repositories Section -->
<section class="page-section bg-light" id="repositories">
  <div class="container">
    <div class="row">
      <div class="col-lg-12 text-center">
        <h2 class="section-heading text-uppercase">GitHub Repositories</h2>
        <h3 class="section-subheading text-muted">Open source projects and research code from Reality Lab</h3>
      </div>
    </div>
    
    <!-- SIDL Featured Image -->
    <div class="row mb-5">
      <div class="col-lg-12 text-center">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
          <img src="{{ site.baseurl }}/assets/img/sidl/dust/input/Case151_D.png" 
               alt="SIDL Benchmark Dataset Overview" 
               class="img-fluid" 
               style="max-height: 400px; width: auto; border-radius: 8px;">
          <p class="mt-3 text-muted" style="font-style: italic;">
            SIDL: Smartphone Dirty Lens Benchmark Dataset for Image Restoration
          </p>
        </div>
      </div>
    </div>
    <div class="row">
      
      <!-- SIDL Benchmark Dataset -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo1">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-eye fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="{{ site.baseurl }}/assets/img/sidl-teaser.png" alt="SIDL Benchmark Dataset">
        </a>
        <div class="portfolio-caption">
          <h4>SIDL Benchmark</h4>
          <p class="text-muted">Smartphone Dirty Lens Dataset</p>
          <p style="color: #007bff; font-weight: bold; margin-top: 8px;">
            🎉 AAAI25 Accept!
          </p>
        </div>
      </div>

      <!-- Main Website Repository -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo2">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-globe fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://opengraph.githubassets.com/1/ssurealitylab-spec/Realitylab-site" alt="Reality Lab Website">
        </a>
        <div class="portfolio-caption">
          <h4>Realitylab-site</h4>
          <p class="text-muted">Main Website Repository</p>
        </div>
      </div>

      <!-- Computer Vision Projects -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo3">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-brain fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://raw.githubusercontent.com/github/explore/main/topics/computer-vision/computer-vision.png" alt="Computer Vision">
        </a>
        <div class="portfolio-caption">
          <h4>Computer Vision</h4>
          <p class="text-muted">Deep Learning & Vision</p>
        </div>
      </div>

      <!-- Robotics & AI -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo4">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-robot fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://raw.githubusercontent.com/github/explore/main/topics/robotics/robotics.png" alt="Robotics">
        </a>
        <div class="portfolio-caption">
          <h4>Robotics & AI</h4>
          <p class="text-muted">Autonomous Systems</p>
        </div>
      </div>

      <!-- Machine Learning -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo5">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-network-wired fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://raw.githubusercontent.com/github/explore/main/topics/machine-learning/machine-learning.png" alt="Machine Learning">
        </a>
        <div class="portfolio-caption">
          <h4>Machine Learning</h4>
          <p class="text-muted">AI Algorithms & Models</p>
        </div>
      </div>

      <!-- Research Papers Code -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo6">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-file-alt fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://raw.githubusercontent.com/github/explore/main/topics/research/research.png" alt="Research">
        </a>
        <div class="portfolio-caption">
          <h4>Research Papers</h4>
          <p class="text-muted">Publication Code</p>
        </div>
      </div>

      <!-- Development Tools -->
      <div class="col-md-4 col-sm-6 portfolio-item">
        <a class="portfolio-link" data-toggle="modal" href="#repo7">
          <div class="portfolio-hover">
            <div class="portfolio-hover-content">
              <i class="fas fa-tools fa-3x"></i>
            </div>
          </div>
          <img class="repo-img img-fluid" src="https://raw.githubusercontent.com/github/explore/main/topics/tools/tools.png" alt="Tools">
        </a>
        <div class="portfolio-caption">
          <h4>Dev Tools</h4>
          <p class="text-muted">Utilities & Libraries</p>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- Repository Modals -->

<!-- Modal 1: SIDL Benchmark -->
<div class="portfolio-modal modal fade" id="repo1" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">SIDL Benchmark</h2>
              <p class="item-intro text-muted">Smartphone Images with Dirty Lenses Dataset</p>
              
              <!-- Contamination Type Toggles -->
              <div class="text-center mb-4">
                <div class="btn-group btn-group-toggle" data-toggle="buttons" id="contaminantTypes">
                  <label class="btn btn-outline-primary active">
                    <input type="radio" name="contaminant" id="dust" value="dust" checked> Dust
                  </label>
                  <label class="btn btn-outline-primary">
                    <input type="radio" name="contaminant" id="finger" value="finger"> Fingerprint
                  </label>
                  <label class="btn btn-outline-primary">
                    <input type="radio" name="contaminant" id="mixed" value="mixed"> Mixed
                  </label>
                  <label class="btn btn-outline-primary">
                    <input type="radio" name="contaminant" id="scratch" value="scratch"> Scratch
                  </label>
                  <label class="btn btn-outline-primary">
                    <input type="radio" name="contaminant" id="water" value="water"> Water
                  </label>
                </div>
              </div>

              <!-- Image Comparison Container -->
              <div class="sidl-comparison-container mb-4" style="position: relative; max-width: 500px; margin: 0 auto;">
                <div class="sidl-image-wrapper" style="position: relative; width: 100%; height: 400px; overflow: hidden; border-radius: 8px; cursor: col-resize;">
                  <!-- Target Image (Base) -->
                  <img id="sidlTargetImage" class="sidl-image" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;" src="{{ site.baseurl }}/assets/img/sidl/dust/target/Case073_D.png" alt="Target Image">
                  
                  <!-- Input Image (Overlay with clip-path) -->
                  <div id="sidlInputContainer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; clip-path: inset(0 50% 0 0);">
                    <img id="sidlInputImage" class="sidl-image" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;" src="{{ site.baseurl }}/assets/img/sidl/dust/input/Case073_D.png" alt="Input Image">
                  </div>
                  
                  <!-- Vertical Divider Line -->
                  <div id="sidlDivider" style="position: absolute; top: 0; left: 50%; width: 2px; height: 100%; background: white; z-index: 10; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>
                  
                  <!-- Slider Handle -->
                  <div id="sidlHandle" style="position: absolute; top: 50%; left: 50%; width: 20px; height: 20px; background: white; border-radius: 50%; transform: translate(-50%, -50%); z-index: 11; box-shadow: 0 0 4px rgba(0,0,0,0.3); cursor: col-resize;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 10px; color: #666;">⟷</div>
                  </div>
                </div>
                
                <!-- Labels -->
                <div class="sidl-labels mt-2">
                  <div class="row">
                    <div class="col-6 text-center">
                      <small class="text-muted"><strong>Input (Contaminated)</strong></small>
                    </div>
                    <div class="col-6 text-center">
                      <small class="text-muted"><strong>Target (Restored)</strong></small>
                    </div>
                  </div>
                </div>
              </div>

              <p><strong>Description:</strong> A novel dataset designed to restore images captured through contaminated smartphone lenses with diverse real-world contaminants.</p>
              <p><strong>Technologies:</strong> Computer Vision, Image Restoration, Machine Learning, Dataset</p>
              <p><strong>Key Features:</strong></p>
              <ul>
                <li>300 static scenes with 1,588 degraded-clean image pairs</li>
                <li>Full ProRAW resolution (4032 × 3024, 12-bit DNG)</li>
                <li>5 contaminant types: fingerprints, dust, scratches, water drops, mixed debris</li>
                <li>Difficulty levels: Easy, Medium, Hard</li>
                <li>Comprehensive evaluation framework</li>
              </ul>
              <div class="text-center">
                <a href="https://sidl-benchmark.github.io/" target="_blank" class="btn btn-primary">
                  <i class="fas fa-globe"></i> Visit Website
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal 2: Main Website -->
<div class="portfolio-modal modal fade" id="repo2" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">Realitylab-site</h2>
              <p class="item-intro text-muted">Main website repository for Reality Lab</p>
              <img class="img-fluid d-block mx-auto" src="https://opengraph.githubassets.com/1/ssurealitylab-spec/Realitylab-site" alt="Realitylab-site">
              <p><strong>Description:</strong> This repository contains the source code for the Reality Lab website built with Jekyll. Features include responsive design, AI chatbot integration, and modern UI/UX.</p>
              <p><strong>Technologies:</strong> Jekyll, HTML5, CSS3, JavaScript, Bootstrap, AI Integration</p>
              <p><strong>Key Features:</strong></p>
              <ul>
                <li>Responsive web design</li>
                <li>AI chatbot with Qwen models</li>
                <li>Research showcase</li>
                <li>Member profiles and publications</li>
              </ul>
              <div class="text-center">
                <a href="https://github.com/ssurealitylab-spec/Realitylab-site" target="_blank" class="btn btn-primary">
                  <i class="fab fa-github"></i> View Repository
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal 3: Computer Vision -->
<div class="portfolio-modal modal fade" id="repo3" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">Computer Vision Projects</h2>
              <p class="item-intro text-muted">Deep learning and computer vision research</p>
              <img class="img-fluid d-block mx-auto" src="https://raw.githubusercontent.com/github/explore/main/topics/computer-vision/computer-vision.png" alt="Computer Vision">
              <p><strong>Research Areas:</strong></p>
              <ul>
                <li>Real-time object detection and tracking</li>
                <li>Semantic segmentation for autonomous vehicles</li>
                <li>Vision-language understanding systems</li>
                <li>3D scene reconstruction</li>
              </ul>
              <p><strong>Publications:</strong> CVPR 2025, BMVC 2025, IEEE Transactions on Robotics</p>
              <div class="text-center">
                <a href="https://github.com/ssurealitylab-spec" target="_blank" class="btn btn-primary">
                  <i class="fab fa-github"></i> View Organization
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal 4: Robotics & AI -->
<div class="portfolio-modal modal fade" id="repo4" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">Robotics & AI</h2>
              <p class="item-intro text-muted">Autonomous systems and human-robot interaction</p>
              <img class="img-fluid d-block mx-auto" src="https://raw.githubusercontent.com/github/explore/main/topics/robotics/robotics.png" alt="Robotics">
              <p><strong>Project Areas:</strong></p>
              <ul>
                <li>Autonomous navigation in dynamic environments</li>
                <li>SLAM (Simultaneous Localization and Mapping)</li>
                <li>Human-robot interaction frameworks</li>
                <li>Multi-agent coordination systems</li>
              </ul>
              <p><strong>Achievements:</strong> ARNOLD Challenge 1st Place, ICRA 2025 acceptance</p>
              <div class="text-center">
                <a href="https://github.com/ssurealitylab-spec" target="_blank" class="btn btn-primary">
                  <i class="fab fa-github"></i> View Organization
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal 5: Machine Learning -->
<div class="portfolio-modal modal fade" id="repo5" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">Research Papers Code</h2>
              <p class="item-intro text-muted">Implementation code for published papers</p>
              <img class="img-fluid d-block mx-auto" src="https://raw.githubusercontent.com/github/explore/main/topics/research/research.png" alt="Research">
              <p><strong>Available Code:</strong></p>
              <ul>
                <li>CVPR 2025: "Advanced Computer Vision for Robotics"</li>
                <li>BMVC 2025: "Multimodal Language Understanding"</li>
                <li>AAAI 2025: "AI+X Healthcare Applications"</li>
                <li>IEEE Robotics: "Real-time Object Detection"</li>
              </ul>
              <p><strong>Datasets:</strong> Annotated datasets and preprocessing tools included</p>
              <div class="text-center">
                <a href="https://github.com/ssurealitylab-spec" target="_blank" class="btn btn-primary">
                  <i class="fab fa-github"></i> View Organization
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </  
    </div>
  </div>
</div>

<!-- Modal 6: Development Tools -->
<div class="portfolio-modal modal fade" id="repo6" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="close-modal" data-dismiss="modal">
        <div class="lr">
          <div class="rl"></div>
        </div>
      </div>
      <div class="container">
        <div class="row">
          <div class="col-lg-8 mx-auto">
            <div class="modal-body">
              <h2 class="text-uppercase">Development Tools</h2>
              <p class="item-intro text-muted">Utilities and libraries for research</p>
              <img class="img-fluid d-block mx-auto" src="https://raw.githubusercontent.com/github/explore/main/topics/tools/tools.png" alt="Tools">
              <p><strong>Available Tools:</strong></p>
              <ul>
                <li>Research experiment tracking frameworks</li>
                <li>Model evaluation and benchmarking tools</li>
                <li>Data visualization libraries</li>
                <li>API wrappers for common ML tasks</li>
              </ul>
              <p><strong>Languages:</strong> Python, JavaScript, C++, CUDA</p>
              <div class="text-center">
                <a href="https://github.com/ssurealitylab-spec" target="_blank" class="btn btn-primary">
                  <i class="fab fa-github"></i> View Organization
                </a>
              </div>
              <button class="btn btn-secondary" data-dismiss="modal" type="button">
                <i class="fas fa-times"></i> Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>