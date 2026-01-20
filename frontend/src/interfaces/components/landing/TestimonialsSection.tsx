import React from 'react';

/**
 * Testimonials Section component
 * Displays user testimonials and reviews
 */
export const TestimonialsSection: React.FC = () => {
  const testimonials = [
    {
      name: "Sarah Johnson",
      role: "CTO at TechStart",
      image: "https://ui-avatars.com/api/?name=Sarah+Johnson&background=6366f1&color=fff&size=128",
      content: "VerifAI has completely transformed how we handle authentication. The clean architecture and security features are exactly what we needed for our enterprise application.",
      rating: 5
    },
    {
      name: "Michael Chen",
      role: "Lead Developer at DevCorp",
      image: "https://ui-avatars.com/api/?name=Michael+Chen&background=8b5cf6&color=fff&size=128",
      content: "The JWT implementation with automatic token refresh is flawless. We've reduced our authentication-related issues by 90% since switching to VerifAI.",
      rating: 5
    },
    {
      name: "Emily Rodriguez",
      role: "Security Engineer at SecureApp",
      image: "https://ui-avatars.com/api/?name=Emily+Rodriguez&background=ec4899&color=fff&size=128",
      content: "As a security professional, I'm impressed by the attention to detail. Token blacklisting, email verification, and RBAC are implemented perfectly.",
      rating: 5
    },
    {
      name: "David Kim",
      role: "Founder at StartupHub",
      image: "https://ui-avatars.com/api/?name=David+Kim&background=10b981&color=fff&size=128",
      content: "The developer experience is outstanding. Clean code, excellent documentation, and a modern tech stack made integration a breeze.",
      rating: 5
    },
    {
      name: "Lisa Anderson",
      role: "Product Manager at InnovateLab",
      image: "https://ui-avatars.com/api/?name=Lisa+Anderson&background=f59e0b&color=fff&size=128",
      content: "Our users love the smooth authentication flow. The email verification and password reset features work flawlessly every time.",
      rating: 5
    },
    {
      name: "James Wilson",
      role: "Full Stack Developer",
      image: "https://ui-avatars.com/api/?name=James+Wilson&background=3b82f6&color=fff&size=128",
      content: "Best authentication solution I've worked with. The clean architecture makes it easy to maintain and extend. Highly recommended!",
      rating: 5
    }
  ];

  return (
    <section id="testimonials" className="py-20 bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-base text-indigo-400 font-semibold tracking-wide uppercase mb-2">
            Testimonials
          </h2>
          <h3 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Trusted by Developers
          </h3>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            See what our users have to say about their experience with VerifAI
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="`bg-linear-to-br` from-slate-800 to-slate-700 p-8 rounded-2xl border border-slate-600 hover:shadow-xl transition-all duration-300"
            >
              {/* Stars */}
              <div className="flex mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <svg
                    key={i}
                    className="w-5 h-5 text-yellow-400 fill-current"
                    viewBox="0 0 20 20"
                  >
                    <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                  </svg>
                ))}
              </div>

              {/* Content */}
              <p className="text-slate-300 mb-6 leading-relaxed italic">
                "{testimonial.content}"
              </p>

              {/* Author */}
              <div className="flex items-center">
                <img
                  src={testimonial.image}
                  alt={testimonial.name}
                  className="w-12 h-12 rounded-full mr-4"
                />
                <div>
                  <h5 className="font-semibold text-white">
                    {testimonial.name}
                  </h5>
                  <p className="text-sm text-slate-400">
                    {testimonial.role}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
