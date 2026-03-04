from flask import Blueprint, render_template, jsonify, session
from database.user_model import User
from database.waste_model import WasteUpload
from database.db import db
from utils.carbon_calculator import CarbonCalculator
from routes.auth_routes import login_required
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)
carbon_calculator = CarbonCalculator()

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard view"""
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def get_stats():
    """Get dashboard statistics for the logged-in user"""
    user_id = session['user_id']
    
    # Get all user uploads
    uploads = WasteUpload.query.filter_by(user_id=user_id).all()
    
    # Basic stats
    total_uploads = len(uploads)
    total_carbon_saved = sum(u.carbon_saved for u in uploads)
    
    # Category distribution
    category_counts = {}
    for upload in uploads:
        category_counts[upload.category] = category_counts.get(upload.category, 0) + 1
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_uploads = WasteUpload.query.filter_by(user_id=user_id)\
                                      .filter(WasteUpload.upload_date >= thirty_days_ago)\
                                      .all()
    
    # Weekly trends
    weekly_data = []
    for i in range(4):  # Last 4 weeks
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        week_uploads = [u for u in uploads if week_start <= u.upload_date < week_end]
        weekly_data.append({
            'week': f'Week {4-i}',
            'count': len(week_uploads),
            'carbon': sum(u.carbon_saved for u in week_uploads)
        })
    
    # Calculate sustainability score
    user = User.query.get(user_id)
    sustainability_score = user.get_sustainability_score()
    
    # Get equivalents
    equivalents = carbon_calculator.get_equivalents(total_carbon_saved)
    
    return jsonify({
        'total_uploads': total_uploads,
        'total_carbon_saved': round(total_carbon_saved, 2),
        'category_distribution': category_counts,
        'weekly_trends': weekly_data,
        'sustainability_score': sustainability_score,
        'equivalents': equivalents,
        'recent_uploads': len(recent_uploads)
    })

@dashboard_bp.route('/api/dashboard/trends/<period>')
@login_required
def get_trends(period):
    """Get trend data for specific period (week/month/year)"""
    user_id = session['user_id']
    
    now = datetime.utcnow()
    
    if period == 'week':
        start_date = now - timedelta(days=7)
        group_by = func.date(WasteUpload.upload_date)
    elif period == 'month':
        start_date = now - timedelta(days=30)
        group_by = func.date(WasteUpload.upload_date)
    elif period == 'year':
        start_date = now - timedelta(days=365)
        group_by = func.strftime('%Y-%m', WasteUpload.upload_date)
    else:
        return jsonify({'error': 'Invalid period'}), 400
    
    # Query trends
    trends = db.session.query(
        group_by.label('date'),
        func.count(WasteUpload.id).label('count'),
        func.sum(WasteUpload.carbon_saved).label('carbon')
    ).filter(
        WasteUpload.user_id == user_id,
        WasteUpload.upload_date >= start_date
    ).group_by(
        group_by
    ).order_by(
        group_by
    ).all()
    
    return jsonify({
        'period': period,
        'data': [{'date': t.date, 'count': t.count, 'carbon': float(t.carbon or 0)} 
                for t in trends]
    })

@dashboard_bp.route('/api/dashboard/leaderboard')
@login_required
def get_leaderboard():
    """Get global leaderboard of top users"""
    # Get top users by carbon saved
    top_users = db.session.query(
        User.username,
        func.count(WasteUpload.id).label('upload_count'),
        func.sum(WasteUpload.carbon_saved).label('total_carbon')
    ).join(WasteUpload).group_by(
        User.id
    ).order_by(
        func.sum(WasteUpload.carbon_saved).desc()
    ).limit(10).all()
    
    # Get current user rank
    user_id = session['user_id']
    user_total = db.session.query(
        func.sum(WasteUpload.carbon_saved)
    ).filter_by(
        user_id=user_id
    ).scalar() or 0
    
    higher_users = db.session.query(
        func.sum(WasteUpload.carbon_saved)
      ).group_by(
          WasteUpload.user_id
      ).having(
          func.sum(WasteUpload.carbon_saved) > user_total
      ).count()
    
    user_rank = higher_users + 1
    
    return jsonify({
        'leaderboard': [
            {'username': u.username, 'uploads': u.upload_count, 
             'carbon': float(u.total_carbon or 0)} 
            for u in top_users
        ],
        'user_rank': user_rank,
        'user_carbon': float(user_total or 0)
    })