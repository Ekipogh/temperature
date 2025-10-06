# Remote Host Deployment Example

# Add this as an alternative to the self-hosted runner approach
# This would go in your .gitea/workflows/ci-cd.yml

  deploy-staging-remote:
    runs-on: ubuntu-latest
    needs: [test, security-scan, code-quality]
    if: |
      contains(github.head_ref, 'feature/') || contains(github.head_ref, 'bugfix/')
    environment:
      name: staging
      url: https://staging.temperature-monitor.example.com
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.DEPLOY_SSH_KEY }}" > ~/.ssh/deploy_key
        chmod 600 ~/.ssh/deploy_key
        ssh-keyscan -H ${{ secrets.DEPLOY_HOST }} >> ~/.ssh/known_hosts

    - name: Create .env file for staging
      run: |
        cat > .env << EOF
        SWITCHBOT_TOKEN=${{ secrets.SWITCHBOT_TOKEN }}
        SWITCHBOT_SECRET=${{ secrets.SWITCHBOT_SECRET }}
        LIVING_ROOM_MAC=${{ secrets.LIVING_ROOM_MAC }}
        BEDROOM_MAC=${{ secrets.BEDROOM_MAC }}
        OFFICE_MAC=${{ secrets.OFFICE_MAC }}
        OUTDOOR_MAC=${{ secrets.OUTDOOR_MAC }}
        TEMPERATURE_INTERVAL=60
        ENVIRONMENT=preprod
        DATABASE_PATH=/app/data/db.sqlite3
        EOF

    - name: Deploy to remote host
      run: |
        # Copy project files to remote host
        rsync -avz --delete \
          -e "ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no" \
          ./ ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }}:${{ secrets.DEPLOY_PATH }}/

        # Execute deployment commands on remote host
        ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no \
          ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} << 'EOF'
          cd ${{ secrets.DEPLOY_PATH }}

          # Stop existing containers
          docker-compose -f ci/docker-compose.preprod.yml down || true

          # Build and start new containers
          docker-compose -f ci/docker-compose.preprod.yml up --build -d

          # Wait and check health
          sleep 30
          docker-compose -f ci/docker-compose.preprod.yml ps

          echo "✅ Remote staging deployment complete"
        EOF

# Required secrets for this approach:
# - DEPLOY_SSH_KEY: Private SSH key for accessing the host
# - DEPLOY_HOST: IP address or hostname of your host machine
# - DEPLOY_USER: Username on the host machine
# - DEPLOY_PATH: Path where the project should be deployed