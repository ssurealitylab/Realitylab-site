---
layout: page
title: Students - Reality Lab | 학생 - 리얼리티랩
description: Graduate students and interns at Reality Lab, Soongsil University. Master's students and research interns working on AI and Computer Vision. 숭실대학교 김희원 교수 연구실 학생.
keywords: Reality Lab students, 리얼리티랩 학생, Soongsil University, 숭실대학교, 숭실대, SSU, Master's students, 석사과정, research interns, 연구 인턴, 김희원, Heewon Kim, 글로벌미디어학부, Computer Vision, Deep Learning, AI researchers, 대학원생
---

# Students

## Ph.D. Students
<p style="color: #6c757d; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px;">Click on a card to view detailed information</p>

<div class="members-grid phd-grid">
  {% for student in site.data.members.students.phd_students %}
  <div class="member-card clickable-card" onclick="openMemberModal('phd-{{ student.name | slugify }}')">
    <div class="member-photo">
      <img src="{{ student.photo }}" alt="{{ student.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
    </div>
    <div class="member-info">
      <h3 class="member-name">{{ student.name }}</h3>
      {% if student.email %}
      <p class="member-email">{{ student.email }}</p>
      {% endif %}
      {% if student.university %}
      <p class="member-university">{{ student.university }}</p>
      {% endif %}
      {% if student.research %}
      <p class="member-research">{{ student.research }}</p>
      {% endif %}
      <div class="member-social">
        {% if student.email and student.email != "" %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation(); copyEmail('{{ student.email }}', event)" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% else %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation()" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% endif %}
        {% if student.github and student.github != "" %}
          <a href="{{ student.github }}" target="_blank" onclick="event.stopPropagation()" title="GitHub">
            <i class="fab fa-github"></i>
          </a>
        {% endif %}
        {% if student.linkedin and student.linkedin != "" %}
          <a href="{{ student.linkedin }}" target="_blank" onclick="event.stopPropagation()" title="LinkedIn">
            <i class="fab fa-linkedin"></i>
          </a>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Modal for {{ student.name }} -->
  <div id="modal-phd-{{ student.name | slugify }}" class="member-modal">
    <div class="modal-content">
      <span class="close-modal" onclick="closeMemberModal('phd-{{ student.name | slugify }}')">&times;</span>
      <div class="modal-photo">
        <img src="{{ student.photo }}" alt="{{ student.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
      </div>
      <div class="modal-info">
        <h2 class="modal-name">{{ student.name }}</h2>
        {% if student.research %}
        <p class="modal-research"><strong>Research:</strong> {{ student.research }}</p>
        {% endif %}

        {% assign phd_news_achievements = "" | split: "" %}
        {% assign phd_pub_achievements = "" | split: "" %}

        {% for news_item in site.data.news.news %}
          {% if news_item.participants contains student.name %}
            {% unless news_item.title contains "Paper Acceptance" %}
              {% assign year = news_item.date | slice: 0, 4 %}
              {% assign news_text = news_item.title | append: " (" | append: year | append: ")" %}
              {% assign phd_news_achievements = phd_news_achievements | push: news_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% for pub in site.data.publications.publications %}
          {% if pub.authors contains student.name %}
            {% unless pub.type == "workshop" and pub.status == "award" %}
              {% assign venue_clean = pub.venue_short | replace: "25", "" | replace: "24", "" | replace: "23", "" | replace: "22", "" | replace: "21", "" | replace: "20", "" %}
              {% assign pub_text = pub.title | append: " - " | append: venue_clean | append: " " | append: pub.year %}
              {% assign phd_pub_achievements = phd_pub_achievements | push: pub_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% if phd_news_achievements.size > 0 or phd_pub_achievements.size > 0 %}
        <div class="modal-achievements">
          <strong>Achievements:</strong>

          {% if phd_news_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Awards & Activities</p>
          <ul style="margin-top: 5px;">
          {% for achievement in phd_news_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}

          {% if phd_pub_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Publications</p>
          <ul style="margin-top: 5px;">
          {% for achievement in phd_pub_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}
        </div>
        {% endif %}

        <div class="modal-social">
          {% if student.github and student.github != "" %}
            <a href="{{ student.github }}" target="_blank" title="GitHub">
              <i class="fab fa-github"></i>
            </a>
          {% endif %}
          {% if student.linkedin and student.linkedin != "" %}
            <a href="{{ student.linkedin }}" target="_blank" title="LinkedIn">
              <i class="fab fa-linkedin"></i>
            </a>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

## Master's Students
<p style="color: #6c757d; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px;">Click on a card to view detailed information</p>

<div class="members-grid">
  {% for student in site.data.members.students.ms_students %}
  <div class="member-card clickable-card" onclick="openMemberModal('{{ student.name | slugify }}')">
    <div class="member-photo">
      <img src="{{ student.photo }}" alt="{{ student.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
    </div>
    <div class="member-info">
      <h3 class="member-name">{{ student.name }}</h3>
      {% if student.email %}
      <p class="member-email">{{ student.email }}</p>
      {% endif %}
      {% if student.university %}
      <p class="member-university">{{ student.university }}</p>
      {% endif %}
      {% if student.research %}
      <p class="member-research">{{ student.research }}</p>
      {% endif %}
      <div class="member-social">
        {% if student.email and student.email != "" %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation(); copyEmail('{{ student.email }}', event)" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% else %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation()" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% endif %}
        {% if student.github and student.github != "" %}
          <a href="{{ student.github }}" target="_blank" onclick="event.stopPropagation()" title="GitHub">
            <i class="fab fa-github"></i>
          </a>
        {% endif %}
        {% if student.linkedin and student.linkedin != "" %}
          <a href="{{ student.linkedin }}" target="_blank" onclick="event.stopPropagation()" title="LinkedIn">
            <i class="fab fa-linkedin"></i>
          </a>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Modal for {{ student.name }} -->
  <div id="modal-{{ student.name | slugify }}" class="member-modal">
    <div class="modal-content">
      <span class="close-modal" onclick="closeMemberModal('{{ student.name | slugify }}')">&times;</span>
      <div class="modal-photo">
        <img src="{{ student.photo }}" alt="{{ student.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
      </div>
      <div class="modal-info">
        <h2 class="modal-name">{{ student.name }}</h2>
        {% if student.research %}
        <p class="modal-research"><strong>Research:</strong> {{ student.research }}</p>
        {% endif %}

        {% comment %} Auto-generate achievements from news and publications {% endcomment %}
        {% assign news_achievements = "" | split: "" %}
        {% assign pub_achievements = "" | split: "" %}

        {% comment %} Collect news achievements (exclude paper acceptances - handled in publications) {% endcomment %}
        {% for news_item in site.data.news.news %}
          {% if news_item.participants contains student.name %}
            {% unless news_item.title contains "Paper Acceptance" %}
              {% assign year = news_item.date | slice: 0, 4 %}
              {% assign news_text = news_item.title | append: " (" | append: year | append: ")" %}
              {% assign news_achievements = news_achievements | push: news_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% comment %} Collect publication achievements (exclude awards/challenges - already in news) {% endcomment %}
        {% for pub in site.data.publications.publications %}
          {% if pub.authors contains student.name %}
            {% comment %} Skip workshop-type awards (they're in news section) {% endcomment %}
            {% unless pub.type == "workshop" and pub.status == "award" %}
              {% comment %} Remove year suffix from venue_short (e.g., CVPR25 -> CVPR) {% endcomment %}
              {% assign venue_clean = pub.venue_short | replace: "25", "" | replace: "24", "" | replace: "23", "" | replace: "22", "" | replace: "21", "" | replace: "20", "" %}
              {% assign pub_text = pub.title | append: " - " | append: venue_clean | append: " " | append: pub.year %}
              {% assign pub_achievements = pub_achievements | push: pub_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% if news_achievements.size > 0 or pub_achievements.size > 0 %}
        <div class="modal-achievements">
          <strong>Achievements:</strong>

          {% if news_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Awards & Activities</p>
          <ul style="margin-top: 5px;">
          {% for achievement in news_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}

          {% if pub_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Publications</p>
          <ul style="margin-top: 5px;">
          {% for achievement in pub_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}
        </div>
        {% endif %}

        <div class="modal-social">
          {% if student.github and student.github != "" %}
            <a href="{{ student.github }}" target="_blank" title="GitHub">
              <i class="fab fa-github"></i>
            </a>
          {% endif %}
          {% if student.linkedin and student.linkedin != "" %}
            <a href="{{ student.linkedin }}" target="_blank" title="LinkedIn">
              <i class="fab fa-linkedin"></i>
            </a>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

## Research Interns
<p style="color: #6c757d; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px;">Click on a card to view detailed information</p>

<div class="members-grid">
  {% for intern in site.data.members.students.interns %}
  <div class="member-card clickable-card" onclick="openMemberModal('intern-{{ intern.name | slugify }}')">
    <div class="member-photo">
      <img src="{{ intern.photo }}" alt="{{ intern.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
    </div>
    <div class="member-info">
      <h3 class="member-name">{{ intern.name }}</h3>
      {% if intern.email %}
      <p class="member-email">{{ intern.email }}</p>
      {% endif %}
      {% if intern.university %}
      <p class="member-university">{{ intern.university }}</p>
      {% endif %}
      {% if intern.research %}
      <p class="member-research">{{ intern.research }}</p>
      {% endif %}
      <div class="member-social">
        {% if intern.email and intern.email != "" %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation(); copyEmail('{{ intern.email }}', event)" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% else %}
          <a href="#" onclick="event.preventDefault(); event.stopPropagation()" title="Email">
            <i class="fas fa-envelope"></i>
          </a>
        {% endif %}
        {% if intern.github and intern.github != "" %}
          <a href="{{ intern.github }}" target="_blank" onclick="event.stopPropagation()" title="GitHub">
            <i class="fab fa-github"></i>
          </a>
        {% endif %}
        {% if intern.linkedin and intern.linkedin != "" %}
          <a href="{{ intern.linkedin }}" target="_blank" onclick="event.stopPropagation()" title="LinkedIn">
            <i class="fab fa-linkedin"></i>
          </a>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Modal for {{ intern.name }} -->
  <div id="modal-intern-{{ intern.name | slugify }}" class="member-modal">
    <div class="modal-content">
      <span class="close-modal" onclick="closeMemberModal('intern-{{ intern.name | slugify }}')">&times;</span>
      <div class="modal-photo">
        <img src="{{ intern.photo }}" alt="{{ intern.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
      </div>
      <div class="modal-info">
        <h2 class="modal-name">{{ intern.name }}</h2>
        {% if intern.research %}
        <p class="modal-research"><strong>Research:</strong> {{ intern.research }}</p>
        {% endif %}

        {% comment %} Auto-generate achievements from news and publications {% endcomment %}
        {% assign intern_news_achievements = "" | split: "" %}
        {% assign intern_pub_achievements = "" | split: "" %}

        {% comment %} Collect news achievements (exclude paper acceptances - handled in publications) {% endcomment %}
        {% for news_item in site.data.news.news %}
          {% if news_item.participants contains intern.name %}
            {% unless news_item.title contains "Paper Acceptance" %}
              {% assign year = news_item.date | slice: 0, 4 %}
              {% assign news_text = news_item.title | append: " (" | append: year | append: ")" %}
              {% assign intern_news_achievements = intern_news_achievements | push: news_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% comment %} Collect publication achievements (exclude awards/challenges - already in news) {% endcomment %}
        {% for pub in site.data.publications.publications %}
          {% if pub.authors contains intern.name %}
            {% comment %} Skip workshop-type awards (they're in news section) {% endcomment %}
            {% unless pub.type == "workshop" and pub.status == "award" %}
              {% comment %} Remove year suffix from venue_short (e.g., CVPR25 -> CVPR) {% endcomment %}
              {% assign venue_clean = pub.venue_short | replace: "25", "" | replace: "24", "" | replace: "23", "" | replace: "22", "" | replace: "21", "" | replace: "20", "" %}
              {% assign pub_text = pub.title | append: " - " | append: venue_clean | append: " " | append: pub.year %}
              {% assign intern_pub_achievements = intern_pub_achievements | push: pub_text %}
            {% endunless %}
          {% endif %}
        {% endfor %}

        {% if intern_news_achievements.size > 0 or intern_pub_achievements.size > 0 %}
        <div class="modal-achievements">
          <strong>Achievements:</strong>

          {% if intern_news_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Awards & Activities</p>
          <ul style="margin-top: 5px;">
          {% for achievement in intern_news_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}

          {% if intern_pub_achievements.size > 0 %}
          <p style="margin: 10px 0 5px 0; font-weight: 600; color: #6c757d; font-size: 0.9rem;">Publications</p>
          <ul style="margin-top: 5px;">
          {% for achievement in intern_pub_achievements %}
            <li>{{ achievement }}</li>
          {% endfor %}
          </ul>
          {% endif %}
        </div>
        {% endif %}

        <div class="modal-social">
          {% if intern.github and intern.github != "" %}
            <a href="{{ intern.github }}" target="_blank" title="GitHub">
              <i class="fab fa-github"></i>
            </a>
          {% endif %}
          {% if intern.linkedin and intern.linkedin != "" %}
            <a href="{{ intern.linkedin }}" target="_blank" title="LinkedIn">
              <i class="fab fa-linkedin"></i>
            </a>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

## Research Robots
<p style="color: #6c757d; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px;">Click on a card to view detailed specifications</p>

<div class="members-grid robots-grid">
  {% for robot in site.data.members.robots.members %}
  <div class="member-card clickable-card" onclick="openMemberModal('robot-{{ robot.name | slugify }}')">
    <div class="member-photo">
      <img src="{{ robot.photo }}" alt="{{ robot.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
    </div>
    <div class="member-info">
      <h3 class="member-name">{{ robot.name }}</h3>
      <p class="member-email"><i class="fas fa-robot"></i> {{ robot.model }}</p>
      <p class="member-university"><i class="fas fa-calendar-alt"></i> Joined: {{ robot.joined }}</p>
      <div class="member-social">
        <a href="#" onclick="event.preventDefault(); event.stopPropagation(); openMemberModal('robot-{{ robot.name | slugify }}')" title="View Specs">
          <i class="fas fa-info-circle"></i>
        </a>
      </div>
    </div>
  </div>

  <!-- Modal for {{ robot.name }} -->
  <div id="modal-robot-{{ robot.name | slugify }}" class="member-modal">
    <div class="modal-content">
      <span class="close-modal" onclick="closeMemberModal('robot-{{ robot.name | slugify }}')">&times;</span>
      <div class="modal-photo">
        <img src="{{ robot.photo }}" alt="{{ robot.name }}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjNmNGY2Ii8+CjxjaXJjbGUgY3g9IjEwMCIgY3k9IjgwIiByPSIzMCIgZmlsbD0iIzllYTNhOCIvPgo8cGF0aCBkPSJNNjAgMTYwYzAtMjIuMDkgMTcuOTEtNDAgNDAtNDBzNDAgMTcuOTEgNDAgNDB2MjBINjB2LTIweiIgZmlsbD0iIzllYTNhOCIvPgo8L3N2Zz4K'">
      </div>
      <div class="modal-info">
        <h2 class="modal-name">{{ robot.name }}</h2>
        <p class="modal-research"><strong>Model:</strong> {{ robot.model }}</p>
        <p class="modal-research"><strong>Joined:</strong> {{ robot.joined }}</p>

        {% if robot.bio %}
        <p class="robot-bio">{{ robot.bio }}</p>
        {% endif %}

        {% if robot.specs %}
        <div class="modal-achievements robot-specs">
          <strong><i class="fas fa-cogs"></i> Specifications</strong>
          <ul class="specs-list">
            {% if robot.specs.height %}<li><span class="spec-label">Height:</span> {{ robot.specs.height }}</li>{% endif %}
            {% if robot.specs.weight %}<li><span class="spec-label">Weight:</span> {{ robot.specs.weight }}</li>{% endif %}
            {% if robot.specs.dof %}<li><span class="spec-label">DoF:</span> {{ robot.specs.dof }}</li>{% endif %}
            {% if robot.specs.speed %}<li><span class="spec-label">Speed:</span> {{ robot.specs.speed }}</li>{% endif %}
            {% if robot.specs.battery %}<li><span class="spec-label">Battery:</span> {{ robot.specs.battery }}</li>{% endif %}
            {% if robot.specs.payload %}<li><span class="spec-label">Payload:</span> {{ robot.specs.payload }}</li>{% endif %}
          </ul>
        </div>
        {% endif %}

      </div>
    </div>
  </div>
  {% endfor %}
</div>

<style>
.members-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-bottom: 50px;
  padding: 20px 0;
}

.members-grid.phd-grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 300px));
  justify-content: start;
}

.member-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.member-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.member-photo {
  margin-bottom: 20px;
}

.member-photo img {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #f8f9fa;
}

.member-name {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
}

.member-research {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 15px;
  line-height: 1.4;
}

.member-achievements {
  text-align: left;
  margin-bottom: 15px;
}

.member-achievements h4 {
  font-size: 0.9rem;
  color: #2c3e50;
  margin-bottom: 8px;
  font-weight: 600;
}

.member-achievements ul {
  font-size: 0.85rem;
  color: #495057;
  margin: 0;
  padding-left: 20px;
}

.member-achievements li {
  margin-bottom: 3px;
}

.member-email {
  font-size: 0.85rem;
  color: #495057;
  margin-bottom: 8px;
  line-height: 1.4;
  font-weight: 500;
}

.member-university {
  font-size: 0.85rem;
  color: #495057;
  margin-bottom: 10px;
  line-height: 1.4;
  font-weight: 500;
}

.member-social {
  display: flex;
  justify-content: center;
  gap: 10px;
  position: relative;
}

.member-social a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  background: #f8f9fa;
  color: #6c757d;
  text-decoration: none;
  transition: all 0.3s ease;
}

.member-social a:hover {
  background: #3498db;
  color: white;
  transform: translateY(-2px);
}

.email-copied-tooltip {
  position: absolute;
  bottom: -35px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.8em;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  z-index: 1000;
  animation: tooltipFadeIn 0.2s ease-out;
  pointer-events: none;
}

.email-copied-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid #667eea;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.clickable-card {
  cursor: pointer;
}

.clickable-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

/* Modal Styles */
.member-modal {
  display: none;
  position: fixed;
  z-index: 9999;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8) !important;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white !important;
  opacity: 1 !important;
  width: 500px;
  max-height: 80vh;
  border-radius: 20px;
  padding: 40px;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
  overflow-y: auto;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.close-modal {
  position: absolute;
  top: 15px;
  right: 20px;
  font-size: 28px;
  font-weight: bold;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
}

.close-modal:hover {
  color: #333;
}

.modal-photo {
  margin-bottom: 25px;
}

.modal-photo img {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #f8f9fa;
}

.modal-name {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 15px;
}

.modal-research {
  font-size: 1rem;
  color: #6c757d;
  margin-bottom: 20px;
  line-height: 1.5;
}

.modal-achievements {
  text-align: left;
  margin-bottom: 25px;
  margin-top: 20px;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 10px;
  word-wrap: break-word;
}

.modal-achievements strong {
  color: #2c3e50;
  font-size: 1.1rem;
  display: block;
  margin-bottom: 12px;
  font-weight: 600;
}

.modal-achievements ul {
  margin: 0;
  padding-left: 20px;
}

.modal-achievements li {
  color: #495057;
  font-size: 0.85rem;
  margin-bottom: 8px;
  line-height: 1.5;
  word-break: keep-all;
  word-wrap: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}

.modal-social {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.modal-social a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #f8f9fa;
  color: #6c757d;
  text-decoration: none;
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

.modal-social a:hover {
  background: #3498db;
  color: white;
  transform: translateY(-3px);
}

h2 {
  color: #2c3e50;
  font-size: 2rem;
  margin-bottom: 20px;
  margin-top: 40px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

h2:first-of-type {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .members-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
  }
  
  .member-card {
    padding: 20px;
  }
  
  .member-photo img {
    width: 100px;
    height: 100px;
  }
  
  .member-name {
    font-size: 1.2rem;
  }
}

/* Robot Section Styles */
.robots-grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 300px));
  justify-content: start;
}

.robot-bio {
  font-size: 0.95rem;
  color: #495057;
  line-height: 1.6;
  margin: 15px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 10px;
}

.robot-specs {
  background: #f8f9fa;
}

.robot-specs strong {
  color: #2c3e50;
}

.robot-specs strong i {
  margin-right: 8px;
}

.specs-list {
  list-style: none !important;
  padding-left: 0 !important;
}

.specs-list li {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e9ecef;
}

.specs-list li:last-child {
  border-bottom: none;
}

.spec-label {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
  margin-right: 10px;
}
</style>

<script>
function openMemberModal(memberId) {
  const modal = document.getElementById('modal-' + memberId);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
  }
}

function closeMemberModal(memberId) {
  const modal = document.getElementById('modal-' + memberId);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto'; // Restore scrolling
  }
}

// Close modal when clicking outside of it
document.addEventListener('click', function(event) {
  if (event.target.classList.contains('member-modal')) {
    event.target.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    const modals = document.querySelectorAll('.member-modal');
    modals.forEach(modal => {
      if (modal.style.display === 'flex') {
        modal.style.display = 'none';
      }
    });
    // Force restore scrolling
    document.body.style.overflow = 'auto';
    document.documentElement.style.overflow = 'auto';
  }
});

function copyEmail(email, event) {
  // Create a temporary textarea element
  const textarea = document.createElement('textarea');
  textarea.value = email;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();

  try {
    // Copy to clipboard
    document.execCommand('copy');

    // Show tooltip below the clicked icon
    showEmailTooltip(event.currentTarget);
  } catch (err) {
    console.error('Failed to copy email:', err);
  }

  document.body.removeChild(textarea);
}

function showEmailTooltip(element) {
  // Remove any existing tooltip
  const existingTooltip = document.querySelector('.email-copied-tooltip');
  if (existingTooltip) {
    existingTooltip.remove();
  }

  // Find the parent member-social container
  const socialLinks = element.closest('.member-social');
  if (!socialLinks) return;

  // Create new tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'email-copied-tooltip';
  tooltip.textContent = '이메일이 복사되었습니다';

  // Append to social-links container
  socialLinks.appendChild(tooltip);

  // Remove tooltip after 2 seconds
  setTimeout(() => {
    tooltip.remove();
  }, 2000);
}
</script>