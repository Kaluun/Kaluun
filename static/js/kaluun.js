/* ============================================================
   KALUUN.JS — Initialisation et corrections Django
   ============================================================ */

// 1. CACHER LE PRELOADER IMMÉDIATEMENT (avant tout le reste)
(function() {
  function hidePreloader() {
    var p = document.getElementById('kaluun-preloader');
    if (p) {
      p.style.transition = 'opacity 0.4s';
      p.style.opacity = '0';
      setTimeout(function() { p.style.display = 'none'; }, 500);
    }
  }
  // Au plus tard 1.5s après le chargement
  if (document.readyState === 'complete') {
    hidePreloader();
  } else {
    window.addEventListener('load', hidePreloader);
    setTimeout(hidePreloader, 1500);
  }
})();

// 2. Stubs pour plugins manquants (évite les crashes de boskery.js)
(function() {
  if (typeof jQuery === 'undefined') return;
  var $ = jQuery;
  if (!$.fn.appear) {
    $.fn.appear = function(fn) { return this.each(function() { try { fn.call(this); } catch(e){} }); };
  }
  if (!$.fn.countTo) {
    $.fn.countTo = function(opts) {
      return this.each(function() {
        var el = $(this), to = opts.to || parseInt(el.data('to')) || 0;
        el.text(to + (opts.suffix || ''));
      });
    };
  }
  if (!$.fn.circleProgress) { $.fn.circleProgress = function() { return this; }; }
  if (!$.fn.niceSelect)     { $.fn.niceSelect     = function() { return this; }; }
  if (!$.fn.isotope)        { $.fn.isotope        = function() { return this; }; }
  if (!$.fn.ajaxChimp)      { $.fn.ajaxChimp      = function() { return this; }; }
  if (!$.fn.validate)       { $.fn.validate       = function() { return this; }; }
})();

// 3. Initialisation jQuery après chargement DOM
$(document).ready(function () {

  /* ─── Auto-dismiss des messages Django ─── */
  $('.kaluun-messages .alert').each(function() {
    var $this = $(this);
    setTimeout(function() { $this.fadeOut(400, function() { $this.remove(); }); }, 5000);
  });

  /* ─── Progress bar about section ─── */
  $('.count-bar').each(function() {
    var pct = $(this).data('percent') || '0%';
    $(this).animate({ width: pct }, 1200);
  });

  /* ─── Boutons quantité produits ─── */
  $(document).on('click', '.quantity-btn.minus', function() {
    var $inp = $(this).siblings('.quantity-input');
    var val = parseInt($inp.val()) - 1;
    if (val >= 1) $inp.val(val);
  });
  $(document).on('click', '.quantity-btn.plus', function() {
    var $inp = $(this).siblings('.quantity-input');
    var max = parseInt($inp.attr('max')) || 99;
    var val = parseInt($inp.val()) + 1;
    if (val <= max) $inp.val(val);
  });

  /* ─── Hero Carousel (OWL) ─── */
  if ($('#hero-carousel-updated').length) {
    $('#hero-carousel-updated').owlCarousel({
      items: 1, loop: true, autoplay: true, autoplayTimeout: 6000,
      animateOut: 'fadeOut', animateIn: 'fadeIn',
      dots: false, nav: false, autoplayHoverPause: true
    });
  }

  /* ─── Testimonials Carousel ─── */
  if ($('#testimonials-carousel').length) {
    $('#testimonials-carousel').owlCarousel({
      items: 3, margin: 30, loop: true, autoplay: true,
      autoplayTimeout: 5000, dots: true, nav: false,
      responsive: { 0: { items: 1 }, 768: { items: 2 }, 1200: { items: 3 } }
    });
  }

  /* ─── Blog Carousel ─── */
  if ($('#blog-carousel').length) {
    var $blogOwl = $('#blog-carousel').owlCarousel({
      items: 3, margin: 20, loop: true, autoplay: false,
      dots: false, nav: false,
      responsive: { 0: { items: 1 }, 768: { items: 2 }, 992: { items: 3 } }
    });
    $('.blog-three__prev').on('click', function() { $blogOwl.trigger('prev.owl.carousel'); });
    $('.blog-three__next').on('click', function() { $blogOwl.trigger('next.owl.carousel'); });
  }

  /* ─── Mobile nav toggle ─── */
  $('.mobile-nav__toggler').on('click', function() {
    $('body').toggleClass('mobile-nav-active');
    $('.mobile-nav__wrapper').toggleClass('open');
  });

  /* ─── WOW.js init ─── */
  if (typeof WOW !== 'undefined') {
    new WOW({ boxClass: 'wow', animateClass: 'animated', offset: 0, mobile: false }).init();
  }

});
